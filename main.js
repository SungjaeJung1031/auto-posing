function vecSetZero(a,anr) {
    anr *= 3;
    a[anr++] = 0.0;
    a[anr++] = 0.0;
    a[anr]   = 0.0;
}

function vecScale(a,anr, scale) {
    anr *= 3;
    a[anr++] *= scale;
    a[anr++] *= scale;
    a[anr]   *= scale;
}

function vecCopy(a,anr, b,bnr) {
    anr *= 3; bnr *= 3;
    a[anr++] = b[bnr++]; 
    a[anr++] = b[bnr++]; 
    a[anr]   = b[bnr];
}

function vecAdd(a,anr, b,bnr, scale = 1.0) {
    anr *= 3; bnr *= 3;
    a[anr++] += b[bnr++] * scale; 
    a[anr++] += b[bnr++] * scale; 
    a[anr]   += b[bnr] * scale;
}

function vecSetDiff(dst,dnr, a,anr, b,bnr, scale = 1.0) {
    dnr *= 3; anr *= 3; bnr *= 3;
    dst[dnr++] = (a[anr++] - b[bnr++]) * scale;
    dst[dnr++] = (a[anr++] - b[bnr++]) * scale;
    dst[dnr]   = (a[anr] - b[bnr]) * scale;
}

function vecLengthSquared(a,anr) {
    anr *= 3;
    let a0 = a[anr], a1 = a[anr + 1], a2 = a[anr + 2];
    return a0 * a0 + a1 * a1 + a2 * a2;
}

function vecDistSquared(a,anr, b,bnr) {
    anr *= 3; bnr *= 3;
    let a0 = a[anr] - b[bnr], a1 = a[anr + 1] - b[bnr + 1], a2 = a[anr + 2] - b[bnr + 2];
    return a0 * a0 + a1 * a1 + a2 * a2;
}	

function vecDot(a,anr, b,bnr) {
    anr *= 3; bnr *= 3;
    return a[anr] * b[bnr] + a[anr + 1] * b[bnr + 1] + a[anr + 2] * b[bnr + 2];
}	

function vecSetCross(a,anr, b,bnr, c,cnr) {
    anr *= 3; bnr *= 3; cnr *= 3;
    a[anr++] = b[bnr + 1] * c[cnr + 2] - b[bnr + 2] * c[cnr + 1];
    a[anr++] = b[bnr + 2] * c[cnr + 0] - b[bnr + 0] * c[cnr + 2];
    a[anr]   = b[bnr + 0] * c[cnr + 1] - b[bnr + 1] * c[cnr + 0];
}			

var gThreeScene;
var gRenderer;
var gCamera;
var gOrbitControl;
var gDragControl;
var gGrabber;
var gMouseDown = false;

const gCubeGeometry = new THREE.BoxGeometry();
//const material: THREE.MeshPhongMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000, transparent: true });
//const cube: THREE.Mesh = new THREE.Mesh(geometry, material);
//scene.add(cube);

const gCubeMaterials = [
    new THREE.MeshPhongMaterial({ color: 0xff0000, transparent: true }),
    new THREE.MeshPhongMaterial({ color: 0x00ff00, transparent: true }),
    new THREE.MeshPhongMaterial({ color: 0x0000ff, transparent: true }),
];

const gCubes = [
    new THREE.Mesh(gCubeGeometry, gCubeMaterials[0]),
    new THREE.Mesh(gCubeGeometry, gCubeMaterials[1]),
    new THREE.Mesh(gCubeGeometry, gCubeMaterials[2]),
];

// ------------------------------------------------------------------

var gPhysicsScene = 
{
    gravity : [0.0, -10.0, 0.0],
    dt : 1.0 / 60.0,
    numSubsteps : 10,
    paused: true,
    objects: [],				
};

// ------------------------------------------------------------------
class SoftBody {
    constructor(tetMesh, scene, edgeCompliance = 100.0, volCompliance = 0.0)
    {
        // physics

        this.numParticles = tetMesh.verts.length / 3;
        this.numTets = tetMesh.tetIds.length / 4;
        this.pos = new Float32Array(tetMesh.verts);
        this.prevPos = tetMesh.verts.slice();
        this.vel = new Float32Array(3 * this.numParticles);

        this.tetIds = tetMesh.tetIds;
        this.edgeIds = tetMesh.tetEdgeIds;
        this.restVol = new Float32Array(this.numTets);
        this.edgeLengths = new Float32Array(this.edgeIds.length / 2);	
        this.invMass = new Float32Array(this.numParticles);

        this.edgeCompliance = edgeCompliance;
        this.volCompliance = volCompliance;

        this.temp = new Float32Array(4 * 3);
        this.grads = new Float32Array(4 * 3);

        this.grabId = -1;
        this.grabInvMass = 0.0;

        this.initPhysics();

        // surface tri mesh

        var geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
        geometry.setIndex(tetMesh.tetSurfaceTriIds);
        var material = new THREE.MeshPhongMaterial({color: 0xF02000});
        material.flatShading = true;
        this.surfaceMesh = new THREE.Mesh(geometry, material);
        this.surfaceMesh.geometry.computeVertexNormals();
        this.surfaceMesh.userData = this;
        this.surfaceMesh.layers.enable(1);
        scene.add(this.surfaceMesh);

        this.volIdOrder = [[1,3,2], [0,2,3], [0,3,1], [0,1,2]];
                    
//					console.log(JSON.stringify(tetMesh.verts));
    }

    translate(x, y, z)
    {
        for (var i = 0; i < this.numParticles; i++) {
            vecAdd(this.pos,i, [x,y,z],0);
            vecAdd(this.prevPos,i, [x,y,z],0);
        }
    }

    updateMeshes() 
    {
        this.surfaceMesh.geometry.computeVertexNormals();
        this.surfaceMesh.geometry.attributes.position.needsUpdate = true;
        this.surfaceMesh.geometry.computeBoundingSphere();									
    }

    getTetVolume(nr) 
    {
        var id0 = this.tetIds[4 * nr];
        var id1 = this.tetIds[4 * nr + 1];
        var id2 = this.tetIds[4 * nr + 2];
        var id3 = this.tetIds[4 * nr + 3];
        vecSetDiff(this.temp,0, this.pos,id1, this.pos,id0);
        vecSetDiff(this.temp,1, this.pos,id2, this.pos,id0);
        vecSetDiff(this.temp,2, this.pos,id3, this.pos,id0);
        vecSetCross(this.temp,3, this.temp,0, this.temp,1);
        return vecDot(this.temp,3, this.temp,2) / 6.0;
    }

    initPhysics() 
    {
        this.invMass.fill(0.0);
        this.restVol.fill(0.0);

        for (var i = 0; i < this.numTets; i++) {
            var vol =this.getTetVolume(i);
            this.restVol[i] = vol;
            var pInvMass = vol > 0.0 ? 1.0 / (vol / 4.0) : 0.0;
            this.invMass[this.tetIds[4 * i]] += pInvMass;
            this.invMass[this.tetIds[4 * i + 1]] += pInvMass;
            this.invMass[this.tetIds[4 * i + 2]] += pInvMass;
            this.invMass[this.tetIds[4 * i + 3]] += pInvMass;
        }
        for (var i = 0; i < this.edgeLengths.length; i++) {
            var id0 = this.edgeIds[2 * i];
            var id1 = this.edgeIds[2 * i + 1];
            this.edgeLengths[i] = Math.sqrt(vecDistSquared(this.pos,id0, this.pos,id1));
        }
    }

    preSolve(dt, gravity)
    {
        for (var i = 0; i < this.numParticles; i++) {
            if (this.invMass[i] == 0.0)
                continue;
            vecAdd(this.vel,i, gravity,0, dt);
            vecCopy(this.prevPos,i, this.pos,i);
            vecAdd(this.pos,i, this.vel,i, dt);
            var y = this.pos[3 * i + 1];
            if (y < 0.0) {
                vecCopy(this.pos,i, this.prevPos,i);
                this.pos[3 * i + 1] = 0.0;
            }
        }
    }

    solve(dt)
    {
        this.solveEdges(this.edgeCompliance, dt);
        this.solveVolumes(this.volCompliance, dt);
    }

    postSolve(dt)
    {
        for (var i = 0; i < this.numParticles; i++) {
            if (this.invMass[i] == 0.0)
                continue;
            vecSetDiff(this.vel,i, this.pos,i, this.prevPos,i, 1.0 / dt);
        }
        this.updateMeshes();
    }

    solveEdges(compliance, dt) {
        var alpha = compliance / dt /dt;

        for (var i = 0; i < this.edgeLengths.length; i++) {
            var id0 = this.edgeIds[2 * i];
            var id1 = this.edgeIds[2 * i + 1];
            var w0 = this.invMass[id0];
            var w1 = this.invMass[id1];
            var w = w0 + w1;
            if (w == 0.0)
                continue;

            vecSetDiff(this.grads,0, this.pos,id0, this.pos,id1);
            var len = Math.sqrt(vecLengthSquared(this.grads,0));
            if (len == 0.0)
                continue;
            vecScale(this.grads,0, 1.0 / len);
            var restLen = this.edgeLengths[i];
            var C = len - restLen;
            var s = -C / (w + alpha);
            vecAdd(this.pos,id0, this.grads,0, s * w0);
            vecAdd(this.pos,id1, this.grads,0, -s * w1);
        }
    }

    solveVolumes(compliance, dt) {
        var alpha = compliance / dt /dt;

        for (var i = 0; i < this.numTets; i++) {
            var w = 0.0;
            
            for (var j = 0; j < 4; j++) {
                var id0 = this.tetIds[4 * i + this.volIdOrder[j][0]];
                var id1 = this.tetIds[4 * i + this.volIdOrder[j][1]];
                var id2 = this.tetIds[4 * i + this.volIdOrder[j][2]];

                vecSetDiff(this.temp,0, this.pos,id1, this.pos,id0);
                vecSetDiff(this.temp,1, this.pos,id2, this.pos,id0);
                vecSetCross(this.grads,j, this.temp,0, this.temp,1);
                vecScale(this.grads,j, 1.0/6.0);

                w += this.invMass[this.tetIds[4 * i + j]] * vecLengthSquared(this.grads,j);
            }
            if (w == 0.0)
                continue;

            var vol = this.getTetVolume(i);
            var restVol = this.restVol[i];
            var C = vol - restVol;
            var s = -C / (w + alpha);

            for (var j = 0; j < 4; j++) {
                var id = this.tetIds[4 * i + j];
                vecAdd(this.pos,id, this.grads,j, s * this.invMass[id])
            }
        }
    }

    squash() {
        for (var i = 0; i < this.numParticles; i++) {
            this.pos[3 * i + 1] = 0.5;
        }
        this.updateMeshes();
    }

    startGrab(pos) 
    {
        var p = [pos.x, pos.y, pos.z];
        var minD2 = Number.MAX_VALUE;
        this.grabId = -1;
        for (let i = 0; i < this.numParticles; i++) {
            var d2 = vecDistSquared(p,0, this.pos,i);
            if (d2 < minD2) {
                minD2 = d2;
                this.grabId = i;
            }
        }

        if (this.grabId >= 0) {
            this.grabInvMass = this.invMass[this.grabId];
            this.invMass[this.grabId] = 0.0;
            vecCopy(this.pos,this.grabId, p,0);	
        }
    }

    moveGrabbed(pos, vel) 
    {
        if (this.grabId >= 0) {
            var p = [pos.x, pos.y, pos.z];
            vecCopy(this.pos,this.grabId, p,0);
        }
    }

    endGrab(pos, vel) 
    {
        if (this.grabId >= 0) {
            this.invMass[this.grabId] = this.grabInvMass;
            var v = [vel.x, vel.y, vel.z];
            vecCopy(this.vel,this.grabId, v,0);
        }
        this.grabId = -1;
    }								
}


// ------------------------------------------------------------------
function simulate() 
{
    if (gPhysicsScene.paused)
        return;

    var sdt = gPhysicsScene.dt / gPhysicsScene.numSubsteps;

    for (var step = 0; step < gPhysicsScene.numSubsteps; step++) {

        for (var i = 0; i < gPhysicsScene.objects.length; i++) 
            gPhysicsScene.objects[i].preSolve(sdt, gPhysicsScene.gravity);
        
        for (var i = 0; i < gPhysicsScene.objects.length; i++) 
            gPhysicsScene.objects[i].solve(sdt);

        for (var i = 0; i < gPhysicsScene.objects.length; i++) 
            gPhysicsScene.objects[i].postSolve(sdt);

    }

    gGrabber.increaseTime(gPhysicsScene.dt);
}

function animate()
{
    requestAnimationFrame(animate)

    gCubes[0].rotation.x += 0.01
    gCubes[0].rotation.y += 0.011
    gCubes[1].rotation.x += 0.012
    gCubes[1].rotation.y += 0.013
    gCubes[2].rotation.x += 0.014
    gCubes[2].rotation.y += 0.015
    //controls.update()
}

// ------------------------------------------
        
function initThreeScene() 
{
    gThreeScene = new THREE.Scene();
    
    // Lights
    
    gThreeScene.add( new THREE.AmbientLight( 0x505050 ) );	
    gThreeScene.add(new THREE.AxesHelper(5));
    gThreeScene.fog = new THREE.Fog( 0x000000, 0, 15 );				

    // var spotLight = new THREE.SpotLight( 0xffffff );
    // spotLight.angle = Math.PI / 5;
    // spotLight.penumbra = 0.2;
    // spotLight.position.set( 2, 3, 3 );
    // spotLight.castShadow = true;
    // spotLight.shadow.camera.near = 3;
    // spotLight.shadow.camera.far = 10;
    // spotLight.shadow.mapSize.width = 1024;
    // spotLight.shadow.mapSize.height = 1024;
    // gThreeScene.add( spotLight );

    var dirLight = new THREE.DirectionalLight( 0x55505a, 1 );
    dirLight.position.set( 0, 3, 0 );
    dirLight.castShadow = true;
    dirLight.shadow.camera.near = 1;
    dirLight.shadow.camera.far = 10;

    dirLight.shadow.camera.right = 1;
    dirLight.shadow.camera.left = - 1;
    dirLight.shadow.camera.top	= 1;
    dirLight.shadow.camera.bottom = - 1;

    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    gThreeScene.add( dirLight );
    
    // Geometry

    var ground = new THREE.Mesh(
        new THREE.PlaneBufferGeometry( 40, 40, 1, 1 ),
        new THREE.MeshPhongMaterial( { color: 0xa0adaf, shininess: 150 } )
    );				

    ground.rotation.x = - Math.PI / 2; // rotates X/Y to X/Z
    ground.receiveShadow = true;
    gThreeScene.add( ground );
    
    var helper = new THREE.GridHelper( 20, 20 );
    helper.material.opacity = 1.0;
    helper.material.transparent = true;
    helper.position.set(0, 0.002, 0);
    gThreeScene.add( helper );				
    
    // Renderer

    gRenderer = new THREE.WebGLRenderer();
    gRenderer.shadowMap.enabled = true;
    gRenderer.setPixelRatio( window.devicePixelRatio );
    gRenderer.setSize( 0.8 * window.innerWidth, 0.8 * window.innerHeight );
    window.addEventListener( 'resize', onWindowResize, false );
    container.appendChild( gRenderer.domElement );
    
    // cubes
    gCubes[0].position.x = -2;
    gCubes[1].position.x = 0;
    gCubes[2].position.x = 2;
    gCubes.forEach((c) => gThreeScene.add(c));

    // Camera
            
    gCamera = new THREE.PerspectiveCamera( 70, window.innerWidth / window.innerHeight, 0.01, 100);
    gCamera.position.set(0, 1, 3);
    gCamera.updateMatrixWorld();	

    gThreeScene.add(gCamera);

    gOrbitControl = new THREE.OrbitControls(gCamera, gRenderer.domElement);
    gOrbitControl.zoomSpeed = 2.0;
    gOrbitControl.panSpeed = 0.4;

    // drag controls
    gDragControl = new THREE.DragControls(gCubes, gCamera, gRenderer.domElement);

    // https://discourse.threejs.org/t/cant-i-use-dragcontrol-and-orbitcontrol-at-the-same-time/4265
    gDragControl.addEventListener( 'dragstart', function () { gOrbitControl.enabled = false; } );
    gDragControl.addEventListener( 'dragend', function () { gOrbitControl.enabled = true; } );
}

// ------- grabber -----------------------------------------------------------

class Grabber {
    constructor() {
        this.raycaster = new THREE.Raycaster();
        this.raycaster.layers.set(1);
        this.raycaster.params.Line.threshold = 0.1;
        this.physicsObject = null;
        this.distance = 0.0;
        this.prevPos = new THREE.Vector3();
        this.vel = new THREE.Vector3();
        this.time = 0.0;
    }
    increaseTime(dt) {
        this.time += dt;
    }
    updateRaycaster(x, y) {
        var rect = gRenderer.domElement.getBoundingClientRect();
        this.mousePos = new THREE.Vector2();
        this.mousePos.x = ((x - rect.left) / rect.width ) * 2 - 1;
        this.mousePos.y = -((y - rect.top) / rect.height ) * 2 + 1;
        this.raycaster.setFromCamera( this.mousePos, gCamera );
    }
    start(x, y) {
        this.physicsObject = null;
        this.updateRaycaster(x, y);
        var intersects = this.raycaster.intersectObjects( gThreeScene.children );
        if (intersects.length > 0) {
            var obj = intersects[0].object.userData;
            if (obj) {
                this.physicsObject = obj;
                this.distance = intersects[0].distance;
                var pos = this.raycaster.ray.origin.clone();
                pos.addScaledVector(this.raycaster.ray.direction, this.distance);
                this.physicsObject.startGrab(pos);
                this.prevPos.copy(pos);
                this.vel.set(0.0, 0.0, 0.0);
                this.time = 0.0;
                if (gPhysicsScene.paused)
                    run();
            }
        }
    }
    move(x, y) {
        if (this.physicsObject) {
            this.updateRaycaster(x, y);
            var pos = this.raycaster.ray.origin.clone();
            pos.addScaledVector(this.raycaster.ray.direction, this.distance);

            this.vel.copy(pos);
            this.vel.sub(this.prevPos);
            if (this.time > 0.0)
                this.vel.divideScalar(this.time);
            else
                this.vel.set(0.0, 0.0, 0.0);
            this.prevPos.copy(pos);
            this.time = 0.0;

            this.physicsObject.moveGrabbed(pos, this.vel);
        }
    }
    end(x, y) {
        if (this.physicsObject) { 
            this.physicsObject.endGrab(this.prevPos, this.vel);
            this.physicsObject = null;
        }
    }
}			

// ------------------------------------------------------

function onWindowResize() {

    gCamera.aspect = window.innerWidth / window.innerHeight;
    gCamera.updateProjectionMatrix();
    gRenderer.setSize( window.innerWidth, window.innerHeight );
}

function run() {
    var button = document.getElementById('buttonRun');
    if (gPhysicsScene.paused)
        button.innerHTML = "Stop";
    else
        button.innerHTML = "Run";
    gPhysicsScene.paused = !gPhysicsScene.paused;
}

function restart() {
    location.reload();
}

function squash() {
    for (var i = 0; i < gPhysicsScene.objects.length; i++)
        gPhysicsScene.objects[i].squash();
    if (!gPhysicsScene.paused)
        run();
}

function newBody() {
    body = new SoftBody(bunnyMesh, gThreeScene);
    body.translate(-1.0 + 2.0 * Math.random(), 0.0, -1.0 + 2.0 * Math.random());
    gPhysicsScene.objects.push(body); 
    
    var numTets = 0;
    for (var i = 0; i < gPhysicsScene.objects.length; i++)
        numTets += gPhysicsScene.objects[i].numTets;
    document.getElementById("numTets").innerHTML = numTets;
}

// make browser to call us repeatedly -----------------------------------

function update() {
    simulate();
    // animate();
    gRenderer.render(gThreeScene, gCamera);
    requestAnimationFrame(update);
}

initThreeScene();
onWindowResize();
update();
			