"use client";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Html, Grid } from "@react-three/drei";
import React, { Suspense } from "react";

export type SceneAsset = {
  id: string;
  name: string;
  category?: string;
  verified?: boolean;
};

export type SceneZone = {
  id: string;
  name: string;
  description?: string;
  floor?: string;
  verified?: boolean;
  x: number;
  z: number;
  width: number;
  depth: number;
  assets?: SceneAsset[];
  asset_count?: number;
};

interface ZoneProps {
  zone: SceneZone;
  selectedId?: string;
  onSelect: (id: string, isZone?: boolean) => void;
}

function Zone({ zone, selectedId, onSelect }: ZoneProps) {
  const assetCount = zone.assets?.length ?? zone.asset_count ?? 0;
  const isZoneSelected = selectedId === zone.id;
  const center: [number, number, number] = [zone.x, 0.06, zone.z];

  return (
    <group position={center}>
      {/* Zone platform */}
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          onSelect(zone.assets?.[0]?.id || zone.id, !zone.assets?.length);
        }}
        receiveShadow
      >
        <boxGeometry args={[zone.width, 0.12, zone.depth]} />
        <meshStandardMaterial
          color={isZoneSelected ? "#bfdbfe" : zone.verified ? "#dbeafe" : "#e7edf5"}
          roughness={0.8}
        />
      </mesh>

      {/* Equipment table / boundary block */}
      <mesh
        position={[0, 0.18, 0]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(zone.assets?.[0]?.id || zone.id, !zone.assets?.length);
        }}
      >
        <boxGeometry args={[Math.max(0.65, zone.width * 0.3), 0.24, Math.max(0.45, zone.depth * 0.25)]} />
        <meshStandardMaterial
          color={isZoneSelected ? "#2563eb" : zone.verified ? "#3b82f6" : "#94a3b8"}
          metalness={0.15}
          roughness={0.5}
        />
      </mesh>

      {/* Zone Label Tag */}
      <Html position={[0, 0.52, 0]} center distanceFactor={11}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect(zone.assets?.[0]?.id || zone.id, !zone.assets?.length);
          }}
          className={`cursor-pointer whitespace-nowrap rounded-lg border px-2.5 py-1 text-[11px] font-semibold shadow-md transition-all hover:scale-105 ${
            isZoneSelected
              ? "border-blue-600 bg-blue-600 text-white"
              : "border-slate-300 bg-white/95 text-slate-800"
          }`}
        >
          {zone.name}
          <span
            className={`ml-1.5 rounded px-1.5 py-0.5 text-[9px] font-bold ${
              isZoneSelected ? "bg-blue-800 text-blue-100" : "bg-slate-100 text-slate-600"
            }`}
          >
            {assetCount}
          </span>
        </button>
      </Html>

      {/* Equipment Hotspot Spheres */}
      {(zone.assets || []).slice(0, 6).map((asset, i) => {
        const isAssetSelected = selectedId === asset.id;
        const px = (i % 3 - 1) * Math.min(0.45, zone.width * 0.18);
        const pz = (Math.floor(i / 3) - 0.3) * Math.min(0.45, zone.depth * 0.22);

        return (
          <group key={asset.id} position={[px, 0.34, pz]}>
            <mesh
              onClick={(e) => {
                e.stopPropagation();
                onSelect(asset.id, false);
              }}
            >
              <sphereGeometry args={[isAssetSelected ? 0.14 : 0.09, 16, 16]} />
              <meshStandardMaterial
                color={isAssetSelected ? "#38bdf8" : asset.verified ? "#059669" : "#d97706"}
                emissive={isAssetSelected ? "#0284c7" : asset.verified ? "#047857" : "#b45309"}
                emissiveIntensity={isAssetSelected ? 0.6 : 0.2}
              />
            </mesh>
            {isAssetSelected && (
              <mesh position={[0, 0.2, 0]}>
                <cylinderGeometry args={[0.02, 0.08, 0.15, 8]} />
                <meshStandardMaterial color="#0284c7" emissive="#38bdf8" emissiveIntensity={0.8} />
              </mesh>
            )}
          </group>
        );
      })}
    </group>
  );
}

export default function LabScene({
  onSelect,
  zones = [],
  selectedId,
  height = "460px"
}: {
  onSelect: (id: string, isZone?: boolean) => void;
  zones?: SceneZone[];
  selectedId?: string;
  height?: string;
}) {
  const visibleZones = zones.length
    ? zones
    : [
        { id: "zone-overview", name: "Laboratory Overview", x: 0, z: 0, width: 2.8, depth: 2.0, assets: [] },
        { id: "zone-computing", name: "High Performance Computing", x: -2.5, z: -1.2, width: 2.2, depth: 1.6, assets: [] },
        { id: "zone-research", name: "AI Research Workspace", x: 2.5, z: -1.2, width: 2.2, depth: 1.6, assets: [] }
      ];

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-inner" style={{ height }}>
      <div className="absolute right-3 top-3 z-10 flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-900/80 px-3 py-1 text-[10px] font-medium text-slate-300 backdrop-blur">
        <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
        Illustrative 3D Digital Twin · Survey Pending
      </div>

      <div className="absolute left-3 top-3 z-10 flex items-center gap-2 rounded-lg bg-slate-900/70 px-2.5 py-1 text-[11px] text-slate-300 backdrop-blur">
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>Verified</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          <span>Unverified</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-sky-400" />
          <span>Selected</span>
        </div>
      </div>

      <Canvas shadows camera={{ position: [7.5, 7.5, 9.5], fov: 40 }}>
        <color attach="background" args={["#f1f5f9"]} />
        <ambientLight intensity={1.2} />
        <directionalLight position={[5, 10, 6]} intensity={2.2} castShadow />
        <Grid args={[24, 24]} cellColor="#cbd5e1" sectionColor="#94a3b8" fadeDistance={24} infiniteGrid />

        {/* Floor foundation */}
        <mesh position={[0, -0.2, 0]} receiveShadow>
          <boxGeometry args={[13, 0.3, 10]} />
          <meshStandardMaterial color="#e2e8f0" roughness={0.9} />
        </mesh>

        {/* Back illustrative wall */}
        <mesh position={[0, 0.8, -4.9]}>
          <boxGeometry args={[13, 1.8, 0.15]} />
          <meshStandardMaterial color="#cbd5e1" roughness={0.7} />
        </mesh>

        {visibleZones.map((z) => (
          <Zone key={z.id} zone={z} selectedId={selectedId} onSelect={onSelect} />
        ))}

        <OrbitControls makeDefault minDistance={4.5} maxDistance={20} maxPolarAngle={Math.PI * 0.48} />
      </Canvas>
    </div>
  );
}
