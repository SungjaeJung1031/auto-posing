var gClock;
var gCamera, gControls, gRenderer;

var gMixer, gSkeletonHelper;

var gScene;
var gSceneKeyPoints;

var gBVH;

const gSphereGeometry = new THREE.SphereGeometry(1);
const gSphereMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000, transparent: true });
var gSpheres = [];

var gOrbitControl;
var gDragControl;

function loadBVH(){
    var loader = new THREE.BVHLoader();
    loader.load( "./100STYLE/Balance/Balance_FW.bvh", function( bvh ){

        gBVH = bvh;

        console.log(gSpheres);

        for (var i = 0 ; i < gBVH.skeleton.bones.length; i++)
        {
            gSpheres.push(new THREE.Mesh(gSphereGeometry, gSphereMaterial));
        }

        gSkeletonHelper = new THREE.SkeletonHelper( bvh.skeleton.bones[ 0 ] );
        gSkeletonHelper.skeleton = bvh.skeleton; // allow animation gMixer to bind to SkeletonHelper directly

        var boneContainer = new THREE.Group();
        boneContainer.add( bvh.skeleton.bones[ 0 ] );

        gScene.add( gSkeletonHelper );
        gScene.add( boneContainer );

        // play animation
        gMixer = new THREE.AnimationMixer( gSkeletonHelper );
        gMixer.clipAction( bvh.clip ).setEffectiveWeight( 1.0 ).play();

    } );
}

function init() {
    gClock = new THREE.Clock();

    gCamera = new THREE.PerspectiveCamera( 60, window.innerWidth / window.innerHeight, 1, 1000 );
    gCamera.position.set( 0, 200, 400 );

    gScene = new THREE.Scene();
    gScene.name = "scene_global"
    gScene.background   = new THREE.Color(0xBAB9B9);
    gScene.add( new THREE.GridHelper( 200, 10 ) );

    gSceneKeyPoints = new THREE.Scene();
    gSceneKeyPoints.name = "scene_keypoints"


    //////////////////////////////////////
    // BVH Loader
    loadBVH();


    //////////////////////////////////////
    // Renderer
    gRenderer = new THREE.WebGLRenderer( { antialias: true } );
    gRenderer.setClearColor( 0xeeeeee );
    gRenderer.setPixelRatio( window.devicePixelRatio );
    gRenderer.setSize( window.innerWidth, window.innerHeight );

    gControls = new THREE.OrbitControls( gCamera , gRenderer.domElement);
    gControls.minDistance = 300;
    gControls.maxDistance = 700;

    document.body.appendChild( gRenderer.domElement );


    //////////////////////////////////////
    // Coltrols
    gOrbitControl =  new THREE.OrbitControls( gCamera, gRenderer.domElement );
    gDragControl = new THREE.DragControls(gSpheres, gCamera, gRenderer.domElement);

    // https://discourse.threejs.org/t/cant-i-use-dragcontrol-and-orbitcontrol-at-the-same-time/4265
    gDragControl.addEventListener( 'dragstart', function () { gOrbitControl.enabled = false; } );
    gDragControl.addEventListener( 'dragend', function () { gOrbitControl.enabled = true; } );

    window.addEventListener( 'resize', onWindowResize, false );

}

function onWindowResize() {

    gCamera.aspect = window.innerWidth / window.innerHeight;
    gCamera.updateProjectionMatrix();

    gRenderer.setSize( window.innerWidth, window.innerHeight );

}

function animate() {

    requestAnimationFrame( animate );
    

    gScene.remove(gSceneKeyPoints);

    while(gSceneKeyPoints.children.length > 0){ 
        gSceneKeyPoints.remove(gSceneKeyPoints.children[0]); 
    }

    var delta = gClock.getDelta();

    if (gBVH)
    {   
        for (var i = 0 ; i < gBVH.skeleton.bones.length; i++)
        {
            gBVH.skeleton.bones[i].getWorldPosition(gSpheres[i].position);
        }
    }
    //console.log(gSpheres[0].position)

    gSpheres.forEach((c) => gSceneKeyPoints.add(c));
        
    gScene.add(gSceneKeyPoints);


    if ( gMixer ) gMixer.update( delta );

    gRenderer.render( gScene, gCamera );

}

init();
animate();