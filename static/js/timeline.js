import * as utility from "./utility.js";

var eraSlider = document.getElementById('timeline-range-filter');
noUiSlider.create(eraSlider, {
    start: [
        + htmx.find('#timeline-range-filter').dataset.start,
        + htmx.find('#timeline-range-filter').dataset.end
    ],
    connect: true,
    range: {
        'min': + htmx.find('#timeline-range-filter').dataset.min,
        'max': + htmx.find('#timeline-range-filter').dataset.max,
    },
});
eraSlider.noUiSlider.on('change', function (values, handle) {
    let year_string = '{{ obj.system.calendar["year_string"]}}';
    htmx.find('#slider-start-value').innerHTML = `${Math.trunc(values[0])} ${year_string}`;
    htmx.find('#slider-end-value').innerHTML = `${Math.trunc(values[1])} ${year_string}`;
});

var map = L.map('timeline-map', {
    crs: L.CRS.Simple,
    minZoom: 0,
    maxZoom: 3,
});
var width = 1792;
var height = 1024;
var bounds = [[0, 0], [height, width]];
var image = L.imageOverlay(htmx.find('#timeline-map-container').dataset.mapurl, bounds).addTo(map);
map.fitBounds(bounds);
map.setMaxBounds(bounds);
var oms = new OverlappingMarkerSpiderfier(map, {
    nearbyDistance: 60,
    circleFootSeparation: 60,
    circleSpiralSwitchover: Infinity,
    keepSpiderfied: true,
});
oms.addListener('spiderfy', function (markers) {
    map.closePopup();
});
oms.addListener('click', function (m) {
    m.openPopup(m.getLatLng());
});

for (let event of htmx.findAll('.unplaced-event-icon')) {
    event.addEventListener('click', function (e) {
        let url = event.querySelector('img').src;
        let eid = event.id;
        console.log(url, eid);
        let center = map.getCenter();
        console.log(center);
        createMarker(map, url, eid, center.lat, center.lng);
        event.closest('.column').classList.add('is-hidden');
    });
}

var page_data = JSON.parse(htmx.find("body").getAttribute('hx-vals'));
var pk = page_data.pk;
var formData = Object.fromEntries(new FormData(htmx.find("#timeline-filters-form")));
formData['daterange'] = eraSlider.noUiSlider.get(true);
formData['user'] = page_data.user;
formData['model'] = page_data.model;
formData['pk'] = page_data.pk;
console.log(formData);
utility.post_data(`/api/timeline/markers`, formData, function (data) {
    console.log(data);
    for (let marker of data.markers) {
        //console.log(marker);
        createMarker(map, marker.imgurl, marker.pk, marker.coordinates.x, marker.coordinates.y, marker.summary);
    }
});

function createMarker(map, url, eid, x, y, popup) {
    var myIcon = L.icon({
        iconUrl: url,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        popupAnchor: [0, -20],
        className: 'event-icon'
    });
    var marker = L.marker([x, y], {
        icon: myIcon,
        riseOnHover: true,
        draggable: true,
        autoPan: true,
        maxWidth: 600,
        minWidth: 150,
        keepInView: true,
    }).addTo(map);
    marker.bindPopup(popup);
    oms.addMarker(marker);
    marker.on('dragend', function (e) {
        let latlng = marker.getLatLng();
        console.log(latlng);
        // Send POST request to /api/timeline
        fetch(`/api/timeline/event/${eid}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                xcoor: latlng.lat,
                ycoor: latlng.lng,
                user: page_data.user,
                model: page_data.model,
                pk: page_data.pk
            })
        });
    });
};;