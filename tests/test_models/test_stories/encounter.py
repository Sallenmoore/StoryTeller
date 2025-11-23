import random

import validators
from autonomous.model.autoattr import IntAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from validators import ValidationError

from autonomous import log
from models.images.image import Image
from models.journal import Journal


class Encounter(AutoModel):
    name = StringAttr(default="")
    backstory = StringAttr(default="")
    desc = StringAttr(default="")
    theme = StringAttr(default="")
    image = ReferenceAttr(choices=[Image])
    world = ReferenceAttr(choices=["World"], required=True)
    associations = ListAttr(ReferenceAttr(choices=["TTRPGBase"]))
    parent = ReferenceAttr(choices=["Place"])
    difficulty = StringAttr(default="")
    enemy_type = StringAttr(default="")
    encounter_type = StringAttr(default="")
    trigger_conditions = StringAttr(default="")
    complications = StringAttr(default="")
    post_scenes = ListAttr(StringAttr(default=""))
    story = ReferenceAttr(choices=["Story"])
    mechanics = StringAttr(default="")
    notes = StringAttr(default="")

    parent_list = ["Location", "City", "District", "Region", "Shop", "Vehicle"]
    _encounter_types = {
        "skill challenge": "Set up a scenario that players will need to roll 3 successful DC CHECKS to complete. A subset of primary skill s>=+1) will have advantage, secondary skills (+0) will be a straight rooll, and other skills (-1) will be at disadvantage. Describe the outcome on 3 fails and the outcome on 3 successes.",
        "combat": "Set up a combat encounter with enemies appropriate to the players' level and abilities. Describe the environment and any obstacles or hazards present. List the enemies present and any special abilities or tactics they may use. Describe the initiative order and any special rules or conditions that apply to the combat.",
        "social interaction": "Set up a social encounter with NPCs that have their own motivations and personalities. Describe the setting and any relevant background information about the NPCs. List the NPCs present and any special abilities or tactics they may use. Describe the goals and objectives of the NPCs and how they may interact with the players",
        "puzzle or trap": "Set up a puzzle or trap that players will need to solve or overcome describe the environment and any clues or hints that may be present list the mechanics of the puzzle or trap and any special rules or conditions that apply describe the consequences of failure and any rewards for success",
        "stealth": "Set up a stealth encounter where players will need to avoid detection by enemies or obstacles describe the environment and any relevant background information about the enemies or obstacles list the enemies or obstacles present and any special abilities or tactics they may use describe the mechanics of stealth and any special rules or conditions that apply describe the consequences of failure and any rewards for success",
    }
    difficulty_list = [
        "trivial",
        "easy",
        "medium",
        "hard",
        "deadly",
    ]
    # {item_type} consistent with
    _items_types = [
        "junk item",
        "trinket or bauble",
        "form of currency",
        "valuable item of no utility, such as gems or art",
        "consumable item, such as food or drink",
        "utility item, such as tools or a map",
        "weapon",
        "armor",
        "unique artifact",
    ]

    _funcobj = {
        "name": "generate_encounter",
        "description": "Generate an Encounter that will challenge players in a TTRPG session",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An evocative title for the encounter",
                },
                "backstory": {
                    "type": "string",
                    "description": "The backstory of the encounter from the antagonists' perspective",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an image of the scene as the characters come upon the encounter ",
                },
                "enemy_type": {
                    "type": "string",
                    "description": "The type of enemies the characters will encounter",
                },
                "difficulty": {
                    "type": "string",
                    "description": "The difficulty of the encounter, which should be one of: trivial, easy, medium, hard, or deadly",
                },
                "complications": {
                    "type": "string",
                    "description": "Additional environmental effects, unforeseen circumstances, or unexpected events that complicate the encounter",
                },
                "post_scenes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Possible scenes or events that could occur immediately following the encounter, depending on the outcome",
                },
                "trigger_conditions": {
                    "type": "string",
                    "description": "What are the conditions that will trigger the encounter?",
                },
                "mechanics": {
                    "type": "string",
                    "description": "What are the specific mechanics or rules that govern the encounter? Are there any associated skill checks or saving throws?",
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional notes or information about running the encounter.",
                },
            },
        },
    }

    ################## Class Methods ##################

    ################## Instance Properties ##################
    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def enemies(self):
        return [*self.creatures, *self.characters]

    @enemies.setter
    def enemies(self, val):
        for enemy in val:
            if enemy.model_name() == "Creature":
                self.creatures.append(enemy)
            elif enemy.model_name() == "Character":
                self.characters.append(enemy)

    @property
    def image_prompt(self):
        enemies = [f"- {e.name} ({e.species}) : {e.desc}" for e in self.enemies]
        enemies_str = "\n".join(enemies)
        return f"""
        A full color illustrated image of the following TTRPG encounter:
        {self.desc}
        {f"with the following preparing: \n{enemies_str}" if self.enemies else ""}
        """

    @property
    def items(self):
        items = [a for a in self.associations if a.model_name() == "Item"]
        for a in self.actors:
            items += [r for r in a.items if r.parent == a]
        if self.parent:
            items += [r for r in self.parent.items if r.parent == self.parent]
        return items

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def campaigns(self):
        return [c for c in self.world.campaigns if self in c.associations]

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def description(self):
        return self.desc

    @description.setter
    def description(self, val):
        self.desc = val

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def vehicles(self):
        return [a for a in self.associations if a.model_name() == "Vehicle"]

    @property
    def genre(self):
        return self.world.genre.lower()

    @property
    def geneology(self):
        geneology = []
        if self.parent:
            geneology.append(self.parent)
            geneology += self.parent.geneology
        return geneology

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def path(self):
        return f"encounter/{self.pk}"

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def shops(self):
        return [a for a in self.associations if a.model_name() == "Shop"]

    @property
    def stories(self):
        stories = [s for s in self.world.stories if self in s.associations]
        return stories

    @property
    def system(self):
        return self.world.system

    @property
    def title(self):
        return self.model_name()

    @property
    def themes_list(self):
        return self.system._themes_list.get(self.model_name().lower())

    @property
    def user(self):
        return self.world.user

    ################## Crud Methods ##################

    def generate(self):
        enemy_type = self.enemy_type or random.choice(["humanoid", "monster", "animal"])
        if story := self.story or random.choice(self.world.stories):
            context = f"An encounter directly or tengentially related to the following storyline: {story.situation} {story.current_status}"
        else:
            context = f"Trouble is brewing in {self.world.name}."

        desc = f"""
- Setting:
    - Genre: {self.genre}
    - World Details: {self.world.history}
    {("- Relevant World Events:" + ("\n    - ".join([s.situation for s in self.stories.events]))) if self.stories and self.stories.events else ""}
"""
        if self.parent and self.parent.desc:
            desc += f"""
    - Type: {self.parent.title}
    - Name: {self.parent.name}
    - Location Backstory: {self.parent.backstory}
     {f"- Controlled By: {self.parent.owner.name}" if hasattr(self.parent, "owner") and self.parent.owner else ""}
    - SETTING DESCRIPTION: {self.parent.desc}
"""
        elif self.desc:
            desc += f"""
- SETTING DESCRIPTION: {self.desc}
"""

        prompt = f"""Generate a {self.genre} TTRPG encounter scenario using the following guidelines:
- CONTEXT: {context}
- ENEMY TYPE: {enemy_type}
- ENCOUNTER TYPE: {self._encounter_types[self.encounter_type] if self.encounter_type in self._encounter_types else "a generic encounter appropriate to the setting and enemy type"}
{f"- NAME: {self.name}" if self.name else ""}
{f"- LOCATION: {desc}" if desc else ""}
{f"- DESCRIPTION: {desc}" if desc else ""}
{f"- THEME: {self.theme}" if self.theme else ""}
{f"- MECHANICS: {self.mechanics}" if self.mechanics else ""}
{f"- SCENARIO: {self.backstory}" if self.backstory else ""}
{f"- DIFFICULTY: {self.difficulty}" if self.difficulty else ""}
{f"- TRIGGER CONDITION: {self.trigger_conditions}" if self.trigger_conditions else ""}
{f"- COMPLICATIONS: {self.complications}" if self.complications else ""}
"""
        # log(prompt, _print=True)
        if associations := self.associations:
            prompt += """
===
- Additional Associated World Elements:
"""
            for ass in associations:
                if ass.name and ass.backstory:
                    prompt += f"""
  - Type: {ass.title}
    - Name: {ass.name}
    - Backstory: {ass.history or ass.backstory}
"""
        if results := self.system.generate(self, prompt=prompt, funcobj=self._funcobj):
            for k, v in results.items():
                setattr(self, k, v)
            self.save()
            self.generate_image()
        log(results, _print=True)
        return results

    def generate_image(self):
        # MARK: generate_image
        if self.image:
            self.image.remove_association(self)
        party = {f"{c.name}.webp": c.image for c in self.players if c.image}
        if image := Image.generate(
            prompt=self.image_prompt, tags=["encounter", self.world.name]
        ):
            self.image = image
            self.image.associations += [self]
            self.image.save()
            self.save()
        else:
            log(self.image_prompt, "Image generation failed.", _print=True)
        return self.image

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(obj.associations), self in obj.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        # log(len(obj.associations), self in obj.associations)

        # log(len(self.associations), obj in self.associations)
        if self.parent and obj.model_name() in self.parent_list:
            self.parent = obj
            self.save()
        return obj

    def add_associations(self, objs):
        for obj in objs:
            self.add_association(obj)
        return self.associations

    def remove_association(self, obj):
        log(
            f"Association: {obj.name}, Removing association: {obj in self.associations}"
        )
        if obj in self.associations:
            # log(f"Removing association: {obj.name} from {self.name}")
            # log(f"Before removal: {len(self.associations)} associations")
            self.associations.remove(obj)
            self.save()
            log(f"After reciprocal removal: {len(self.associations)} associations")
        log(
            f"Associations: {obj.name}, Removed association: {obj not in self.associations}"
        )
        return self.associations

    def has_associations(self, model):
        log(model)
        if not isinstance(model, str):
            model = model.__name__
        for assoc in self.associations:
            if assoc.model_name() == model:
                return True
        return False

    ################## Instance Methods ##################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "image": str(self.image.url()) if self.image else "",
            "name": self.name,
            "backstory": self.backstory,
            "difficulty": self.difficulty,
            "desc": self.desc,
            "theme": self.theme,
            "parent": {"name": self.parent.name, "pk": str(self.parent.pk)}
            if self.parent
            else None,
            "enemy_type": self.enemy_type,
            "encounter_type": self.encounter_type,
            "trigger_conditions": self.trigger_conditions,
            "complications": self.complications,
            "post_scenes": self.post_scenes,
            "story": {"name": self.story.name, "pk": str(self.story.pk)}
            if self.story
            else None,
            "mechanics": self.mechanics,
            "notes": self.notes,
            "creatures": [{"name": r.name, "pk": str(r.pk)} for r in self.creatures],
            "characters": [{"name": r.name, "pk": str(r.pk)} for r in self.characters],
            "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_image()
        document.pre_save_traits()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################

    def pre_save_image(self):
        if isinstance(self.image, str):
            if validators.url(self.image):
                self.image = Image.from_url(
                    self.image,
                    prompt=self.image_prompt,
                    tags=[*self.image_tags],
                )
                self.image.save()
            elif image := Image.get(self.image):
                self.image = image
            else:
                raise ValidationError(
                    f"Image must be an Image object, url, or Image pk, not {self.image}"
                )
        elif self.image and not self.image.tags:
            self.image.tags = self.image_tags
            self.image.save()

        if self.image and self not in self.image.associations:
            self.image.associations += [self]
            self.image.save()

    def pre_save_traits(self):
        if not self.theme:
            self.theme = f"{random.choice(self.themes_list['themes'])}; {random.choice(self.themes_list['motifs'])}"
