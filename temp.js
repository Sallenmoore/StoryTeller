// Define the API endpoint
const apiUrl = "https://storyteller.stevenamoore.dev/675b466df635f481380f6879/list/vehicle";

// Fetch obj data from the API
fetch(apiUrl, { mode: 'cors' })
    .then(response => { return response.json(); })
    .then(data => {
        console.log(typeof data, data);
        for (obj of data) {
            console.log(obj['name'], typeof obj);
            if (obj.name) {
                // Check if a obj with the same name already exists
                const existingActor = game.actors.find(actor => actor.name === obj.name);
                console.log(obj);
                // Prepare obj data
                const objData = {
                    name: obj.name,
                    img: obj.img,
                    data: {
                        ac: obj.ac,
                        hp: obj.hitpoints,
                        attributes: {
                            strength: obj.strength,
                            dexterity: obj.dexterity,
                            constitution: obj.constitution,
                            intelligence: obj.intelligence,
                            wisdom: obj.wisdom,
                            charisma: obj.charisma,
                        }
                    }
                };

                if (existingActor) {
                    // Update existing obj
                    existingActor.update(objData.data);
                    ui.notifications.info(`Updated obj: ${objData.name}`);
                } else {
                    // Create a new obj
                    const templateactor = game.actors.find(actor => actor.name === "sample_vehicle");
                    Actor.create(templateactor).then(a => {
                        a.update(objData);
                    });
                    ui.notifications.info(`Created new obj: ${objData.name}`);
                }
            }
        }
    })
    .catch(error => {
        console.error("Error fetching obj data:", error);
    });