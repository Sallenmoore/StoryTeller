import * as THREE from 'three';

var autogm = document.getElementById("autogm-3d");
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, autogm.innerWidth / autogm.innerHeight, 0.1, 1000);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(autogm.innerWidth, autogm.innerHeight);
autogm.appendChild(renderer.domElement);

const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
const cube = new THREE.Mesh(geometry, material);

scene.add(cube);

camera.position.z = 5;

function animate() {
    renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);
console.log("Autogm 3D renderer initialized");