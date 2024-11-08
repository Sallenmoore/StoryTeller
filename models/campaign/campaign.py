# from autonomous.model.autoattr import AutoAttribute
import markdown

from autonomous import log
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.events.event import Event

from .session import Session


class Campaign(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    world = ReferenceAttr(choices=["World"], required=True)
    sessions = ListAttr(ReferenceAttr(choices=[Session]))
    players = ListAttr(ReferenceAttr(choices=["Character"]), default=list)
    summary = StringAttr(default="")
    current_episode = ReferenceAttr(choices=[Session])
    canon = ListAttr(ReferenceAttr(choices=[Event]))

    def delete(self):
        all(e.delete() for e in self.sessions)
        super().delete()

    ## MARK: Properties
    ##################### PROPERTY METHODS ####################
    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def pois(self):
        return [a for a in self.associations if a.model_name() == "POI"]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def associations(self):
        associated_objects = []
        for episode in self.sessions:
            for obj in episode.associations:
                if obj not in associated_objects:
                    associated_objects.append(obj)
        return associated_objects

    @property
    def episodes(self):
        return self.sessions

    @property
    def events(self):
        return self.canon

    @episodes.setter
    def episodes(self, value):
        self.sessions = value

    @property
    def end_date(self):
        if self.sessions:
            for session in self.sessions:
                if session.end_date:
                    return session.end_date

    @property
    def start_date(self):
        if self.sessions:
            for session in self.sessions[::-1]:
                if session.start_date:
                    return session.start_date

    @property
    def session_reports(self):
        reports = []
        for session in self.sessions:
            reports.append(session.session_report)
        return reports

    ## MARK: INSTANCE METHODS
    ################################################################
    ##                     INSTANCE METHODS                       ##
    ################################################################
    def resummarize(self):
        text = ""
        for entry in sorted(self.sessions, key=lambda x: x.name):
            if entry.summary.strip():
                text += f"\n{entry.summary}\n"
            elif entry.start_date.year:
                entry.resummarize()
        if text:
            self.summary = self.world.system.generate_summary(
                text,
                primer="Generate a summary of the campaign events in MARKDOWN format with a paragraph breaks where appropriate, but after no more than 4 sentences.",
            )
            self.summary = self.summary.replace("```markdown", "").replace("```", "")
            self.summary = (
                markdown.markdown(self.summary)
                .replace("h1>", "h3>")
                .replace("h2>", "h3>")
            )
            self.save()

    def add_session(
        self,
        name=None,
        description=None,
        start_date=None,
        end_date=None,
        report=None,
    ):
        episode = Session(
            campaign=self,
            name=f"Episode {len(self.sessions) + 1}: [Title]",
        )
        episode.save()
        self.sessions += [episode]
        self.save()
        return self.update_session(
            pk=episode.pk,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            report=report,
        )

    def update_session(
        self,
        pk,
        name=None,
        description=None,
        start_date=None,
        end_date=None,
        report=None,
    ):
        if session := Session.get(pk):
            session.name = session.name if name is None else name
            session.description = (
                session.description if description is None else description
            )
            session.start_date = (
                session.start_date if start_date is None else start_date
            )
            session.end_date = session.end_date if end_date is None else end_date
            if report != session.session_report:
                session.session_report = report
            session.save()
            self.save()
        else:
            raise ValueError("Session not found in campaign")
        return session

    def add_association(self, session, obj):
        return session.add_association(obj)

    def get_episode(self, sessionpk=None):
        return self.get_session(sessionpk)

    def get_session(self, sessionpk=None):
        session = Session.get(sessionpk)
        if session in self.sessions:
            return session
        else:
            return None

    def delete_session(self, sessionpk):
        session = Session.get(sessionpk)
        if session in self.sessions:
            self.sessions.remove(session)
            session.delete()
            self.summary = ""
            self.save()

    def set_as_canon(self, event):
        if event in self.canon:
            log(f"Event already canonized {event}")
        elif isinstance(event, Event):
            self.canon += [event]
        elif isinstance(event, list):
            (self.set_as_canon(e) for e in event)
        elif hasattr(event, "events"):
            (self.set_as_canon(e) for e in event.events)
        else:
            log(f"Cannot set {event} as a canonized event")
        self.save()

    def page_data(self):
        data = {
            "name": self.name,
            "description": self.description,
            "summary": self.summary,
        }
        data["start_date"] = self.start_date.datestr() if self.start_date else "Unknown"
        data["end_date"] = self.end_date.datestr() if self.end_date else "Ongoing"
        return data

    # MARK: Verification
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_current_episode()
        document.pre_save_episodes()
        document.pre_save_players()
        document.pre_save_canon()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # log([p.name for p in document.players])

    # def clean(self):
    #     super().clean()

    ################### Verification Methods ###################

    def pre_save_current_episode(self):
        if not self.current_episode and self.sessions:
            self.current_episode = self.sessions[0]

    def pre_save_episodes(self):
        sess = []
        for s in self.sessions:
            if s not in sess:
                sess.append(s)
        self.sessions = sorted(sess, key=lambda x: x.episode_num, reverse=True)

    def pre_save_players(self):
        for p in self.players:
            if not p.pk:
                log(f"{p} is unsaved. Saving....")
                p.save()

    def pre_save_canon(self):
        self.canon = [e for s in self.episodes for e in s.events]
        self.canon.sort()
