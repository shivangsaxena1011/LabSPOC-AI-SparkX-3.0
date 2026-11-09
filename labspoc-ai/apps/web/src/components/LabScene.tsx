"use client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html, Grid } from "@react-three/drei";
import { Suspense } from "react";

type SceneAsset = { id:string; name:string; category?:string; verified?:boolean };
type SceneZone = { id:string; name:string; description?:string; floor?:string; verified?:boolean; x:number; z:number; width:number; depth:number; assets?:SceneAsset[]; asset_count?:number };

function Zone({zone,onSelect}:{zone:SceneZone;onSelect:(id:string)=>void}) {
  const assetCount = zone.assets?.length ?? zone.asset_count ?? 0;
  const center:[number,number,number] = [zone.x,0.06,zone.z];
  return <group position={center}>
    <mesh onClick={()=>onSelect(zone.assets?.[0]?.id || zone.id)} receiveShadow>
      <boxGeometry args={[zone.width,.12,zone.depth]}/>
      <meshStandardMaterial color={zone.verified?"#dbeafe":"#e7edf5"} roughness={.9}/>
    </mesh>
    <mesh position={[0,.18,0]} onClick={()=>onSelect(zone.assets?.[0]?.id || zone.id)}>
      <boxGeometry args={[Math.max(.65,zone.width*.25),.24,Math.max(.45,zone.depth*.22)]}/>
      <meshStandardMaterial color={zone.verified?"#4777c8":"#9aa9bd"} metalness={.12} roughness={.6}/>
    </mesh>
    <Html position={[0,.48,0]} center distanceFactor={10}>
      <button onClick={()=>onSelect(zone.assets?.[0]?.id || zone.id)} className="whitespace-nowrap rounded-lg border border-slate-200 bg-white/95 px-2.5 py-1.5 text-[10px] font-semibold text-slate-800 shadow-lg">
        {zone.name}<span className="ml-1.5 rounded bg-slate-100 px-1 py-0.5 text-[9px] text-slate-500">{assetCount}</span>
      </button>
    </Html>
    {(zone.assets||[]).slice(0,5).map((asset,i)=>{
      const px = (i%3-1)*Math.min(.42,zone.width*.16);
      const pz = (Math.floor(i/3)-.3)*Math.min(.42,zone.depth*.2);
      return <mesh key={asset.id} position={[px,.34,pz]} onClick={()=>onSelect(asset.id)}>
        <sphereGeometry args={[.09,16,16]}/><meshStandardMaterial color={asset.verified?"#0f9f86":"#d18a35"} emissive={asset.verified?"#0f766e":"#92400e"} emissiveIntensity={.18}/>
      </mesh>
    })}
  </group>
}

export default function LabScene({onSelect,zones=[]}:{onSelect:(id:string)=>void;zones?:SceneZone[]}){
 const visibleZones = zones.length ? zones : [
  {id:"zone-overview",name:"Laboratory overview",x:0,z:0,width:2.6,depth:2,assets:[]},
  {id:"zone-computing",name:"Computing systems",x:-2,z:-1,width:2,depth:1.5,assets:[]},
  {id:"zone-research",name:"Research workspace",x:2,z:-1,width:2,depth:1.5,assets:[]}
 ];
 return <div className="h-[440px] w-full overflow-hidden rounded-xl bg-slate-950">
  <Canvas shadows camera={{position:[7,7,9],fov:42}}>
   <color attach="background" args={["#edf2f8"]}/>
   <ambientLight intensity={1.15}/><directionalLight position={[4,9,5]} intensity={2} castShadow/>
   <Grid args={[24,24]} cellColor="#d3dce8" sectionColor="#9aaac0" fadeDistance={22} infiniteGrid/>
   <mesh position={[0,-.22,0]} receiveShadow><boxGeometry args={[12,.3,9]}/><meshStandardMaterial color="#dce4ef"/></mesh>
   <mesh position={[0,.7,-4.35]}><boxGeometry args={[12,1.4,.12]}/><meshStandardMaterial color="#b7c5d8"/></mesh>
   {visibleZones.map(z=><Zone key={z.id} zone={z} onSelect={onSelect}/>)}
   <OrbitControls makeDefault minDistance={5} maxDistance={18} maxPolarAngle={Math.PI*.48}/>
  </Canvas>
 </div>
}
