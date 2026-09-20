import React, { useEffect, useRef, useState } from "react";
import type { PlacedFixture, RoomLayout } from "../types";

interface Bathroom3DCanvasProps {
  layout: RoomLayout;
  selectedProductId?: string | null;
  onSelectProduct?: (productId: string) => void;
}

const FIXTURE_3D_COLORS: Record<string, { top: string; front: string; side: string }> = {
  vanity: { top: "#b89f82", front: "#8a7055", side: "#6c5740" },
  basin: { top: "#f4f3f0", front: "#dedcd7", side: "#c7c4be" },
  toilet: { top: "#f8f9fa", front: "#e2e6ea", side: "#cfd4da" },
  smart_toilet: { top: "#f0f4f8", front: "#d9e2ec", side: "#bcccdc" },
  shower: { top: "#93c5fd33", front: "#60a5fa44", side: "#3b82f655" }, // glass translucent
  smart_shower: { top: "#a7f3d033", front: "#34d39944", side: "#10b98155" },
  bathtub: { top: "#f1f5f9", front: "#cbd5e1", side: "#94a3b8" },
  storage: { top: "#71717a", front: "#52525b", side: "#3f3f46" },
  mirror: { top: "#e0e7ff", front: "#c7d2fe", side: "#a5b4fc" },
};

export const Bathroom3DCanvas: React.FC<Bathroom3DCanvasProps> = ({
  layout,
  selectedProductId,
  onSelectProduct,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Orbit camera state
  const [yaw, setYaw] = useState<number>(45); // degrees horizontal
  const [pitch, setPitch] = useState<number>(35); // degrees vertical
  const [zoom, setZoom] = useState<number>(1.1);
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  // Canvas interaction
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleClick = () => {
    if (layout.placed.length > 0 && onSelectProduct) {
      // Allow cycling through or selecting the first fixture
      const nextFixture = layout.placed.find((p) => p.product_id !== selectedProductId);
      if (nextFixture) {
        onSelectProduct(nextFixture.product_id);
      }
    }
  };


  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    setYaw((prev) => (prev + dx * 0.6) % 360);
    setPitch((prev) => Math.max(10, Math.min(80, prev - dy * 0.4)));
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    setZoom((prev) => Math.max(0.6, Math.min(2.2, prev - e.deltaY * 0.001)));
  };

  // Render 3D Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high-DPI displays
    const rect = canvas.getBoundingClientRect();
    const width = rect.width || 600;
    const height = rect.height || 420;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const roomW = layout.room_width_in || 72;
    const roomL = layout.room_length_in || 96;
    const roomH = 96; // 8ft ceiling

    // Camera angles to radians
    const radYaw = ((yaw + 90) * Math.PI) / 180;
    const radPitch = (pitch * Math.PI) / 180;

    const cosYaw = Math.cos(radYaw);
    const sinYaw = Math.sin(radYaw);
    const cosPitch = Math.cos(radPitch);
    const sinPitch = Math.sin(radPitch);

    const cx = width / 2;
    const cy = height / 2 + 30;
    const baseScale = (Math.min(width, height) / (Math.max(roomW, roomL) * 1.5)) * zoom;

    // 3D Point projection function
    // Coordinates: x in [0, roomW], y in [0, roomL], z in [0, roomH]
    const project = (x: number, y: number, z: number) => {
      // Center origin
      const rx = x - roomW / 2;
      const ry = y - roomL / 2;
      const rz = z;

      // Rotate Y (yaw)
      const x1 = rx * cosYaw - ry * sinYaw;
      const y1 = rx * sinYaw + ry * cosYaw;

      // Rotate X (pitch)
      const x2 = x1;
      const y2 = y1 * sinPitch - rz * cosPitch;
      const z2 = y1 * cosPitch + rz * sinPitch;

      // Isometric / weak perspective projection
      const px = cx + x2 * baseScale;
      const py = cy + y2 * baseScale;

      return { x: px, y: py, depth: z2 };
    };

    // Draw Floor with tile pattern
    const fP0 = project(0, 0, 0);
    const fP1 = project(roomW, 0, 0);
    const fP2 = project(roomW, roomL, 0);
    const fP3 = project(0, roomL, 0);

    ctx.beginPath();
    ctx.moveTo(fP0.x, fP0.y);
    ctx.lineTo(fP1.x, fP1.y);
    ctx.lineTo(fP2.x, fP2.y);
    ctx.lineTo(fP3.x, fP3.y);
    ctx.closePath();

    // Floor fill
    const floorGrad = ctx.createLinearGradient(fP0.x, fP0.y, fP2.x, fP2.y);
    floorGrad.addColorStop(0, "#eceae4");
    floorGrad.addColorStop(1, "#dfdcd4");
    ctx.fillStyle = floorGrad;
    ctx.fill();
    ctx.strokeStyle = "#c8c4b8";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Floor grid lines (tiles every 12 inches)
    ctx.save();
    ctx.strokeStyle = "rgba(180, 175, 165, 0.4)";
    ctx.lineWidth = 0.8;
    for (let gx = 12; gx < roomW; gx += 12) {
      const pA = project(gx, 0, 0);
      const pB = project(gx, roomL, 0);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();
    }
    for (let gy = 12; gy < roomL; gy += 12) {
      const pA = project(0, gy, 0);
      const pB = project(roomW, gy, 0);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();
    }
    ctx.restore();

    // Back walls (draw only back facing walls based on camera angle)
    const drawWall = (
      p1: { x: number; y: number },
      p2: { x: number; y: number },
      p3: { x: number; y: number },
      p4: { x: number; y: number },
      color: string
    ) => {
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.lineTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "rgba(180, 175, 165, 0.6)";
      ctx.lineWidth = 1;
      ctx.stroke();
    };

    // 4 Corner Ceiling points
    const cP0 = project(0, 0, roomH);
    const cP1 = project(roomW, 0, roomH);
    const cP2 = project(roomW, roomL, roomH);
    const cP3 = project(0, roomL, roomH);

    // North wall (y = 0)
    if (sinYaw > -0.2) {
      drawWall(fP0, fP1, cP1, cP0, "#f5f3ee");
    }
    // West wall (x = 0)
    if (cosYaw < 0.2) {
      drawWall(fP3, fP0, cP0, cP3, "#ece9e1");
    }
    // South wall (y = roomL)
    if (sinYaw < 0.2) {
      drawWall(fP2, fP3, cP3, cP2, "#f7f5ef");
    }
    // East wall (x = roomW)
    if (cosYaw > -0.2) {
      drawWall(fP1, fP2, cP2, cP1, "#e8e5dc");
    }

    // Clearance envelopes on the floor
    layout.placed.forEach((item) => {
      const cx0 = item.clearance.x_in;
      const cy0 = item.clearance.y_in;
      const cx1 = cx0 + item.clearance.width_in;
      const cy1 = cy0 + item.clearance.depth_in;

      const cp0 = project(cx0, cy0, 0.5);
      const cp1 = project(cx1, cy0, 0.5);
      const cp2 = project(cx1, cy1, 0.5);
      const cp3 = project(cx0, cy1, 0.5);

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(cp0.x, cp0.y);
      ctx.lineTo(cp1.x, cp1.y);
      ctx.lineTo(cp2.x, cp2.y);
      ctx.lineTo(cp3.x, cp3.y);
      ctx.closePath();
      ctx.fillStyle = "rgba(31, 107, 74, 0.08)";
      ctx.fill();
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = "rgba(31, 107, 74, 0.4)";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();
    });

    // Sort 3D Fixture boxes back-to-front (Painter's algorithm)
    const sortedFixtures = [...layout.placed].sort((a, b) => {
      const centerA = project(
        a.footprint.x_in + a.footprint.width_in / 2,
        a.footprint.y_in + a.footprint.depth_in / 2,
        15
      );
      const centerB = project(
        b.footprint.x_in + b.footprint.width_in / 2,
        b.footprint.y_in + b.footprint.depth_in / 2,
        15
      );
      return centerB.depth - centerA.depth;
    });

    // Render 3D Fixture Boxes
    sortedFixtures.forEach((fixture: PlacedFixture) => {
      const isSelected = selectedProductId === fixture.product_id;
      const x0 = fixture.footprint.x_in;
      const y0 = fixture.footprint.y_in;
      const w = fixture.footprint.width_in;
      const d = fixture.footprint.depth_in;

      // Fixture height by category
      let h = 34; // default vanity/counter
      let zBase = 0;
      if (fixture.category === "toilet" || fixture.category === "smart_toilet") {
        h = 28;
      } else if (fixture.category === "shower" || fixture.category === "smart_shower") {
        h = 78; // full enclosure
      } else if (fixture.category === "bathtub") {
        h = 22;
      } else if (fixture.category === "mirror") {
        zBase = 46;
        h = 36;
      } else if (fixture.category === "basin") {
        zBase = 32;
        h = 6;
      }

      const x1 = x0 + w;
      const y1 = y0 + d;
      const z0 = zBase;
      const z1 = zBase + h;

      // 8 Bounding vertices
      const v100 = project(x1, y0, z0);
      const v110 = project(x1, y1, z0);
      const v010 = project(x0, y1, z0);

      const v001 = project(x0, y0, z1);
      const v101 = project(x1, y0, z1);
      const v111 = project(x1, y1, z1);
      const v011 = project(x0, y1, z1);

      const palette = FIXTURE_3D_COLORS[fixture.category] || {
        top: "#d1d5db",
        front: "#9ca3af",
        side: "#6b7280",
      };

      // Draw Top Face
      ctx.beginPath();
      ctx.moveTo(v001.x, v001.y);
      ctx.lineTo(v101.x, v101.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v011.x, v011.y);
      ctx.closePath();
      ctx.fillStyle = isSelected ? "#3b82f6" : palette.top;
      ctx.fill();
      ctx.strokeStyle = isSelected ? "#1d4ed8" : "rgba(0,0,0,0.15)";
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Draw South/Front Face
      ctx.beginPath();
      ctx.moveTo(v010.x, v010.y);
      ctx.lineTo(v110.x, v110.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v011.x, v011.y);
      ctx.closePath();
      ctx.fillStyle = isSelected ? "#2563eb" : palette.front;
      ctx.fill();
      ctx.strokeStyle = isSelected ? "#1d4ed8" : "rgba(0,0,0,0.15)";
      ctx.stroke();

      // Draw East/Side Face
      ctx.beginPath();
      ctx.moveTo(v100.x, v100.y);
      ctx.lineTo(v110.x, v110.y);
      ctx.lineTo(v111.x, v111.y);
      ctx.lineTo(v101.x, v101.y);
      ctx.closePath();
      ctx.fillStyle = isSelected ? "#1d4ed8" : palette.side;
      ctx.fill();
      ctx.strokeStyle = isSelected ? "#1d4ed8" : "rgba(0,0,0,0.15)";
      ctx.stroke();

      // Label on top of fixture
      const centerTop = project(x0 + w / 2, y0 + d / 2, z1);
      ctx.save();
      ctx.font = "bold 10px 'Inter', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = isSelected ? "#ffffff" : "#1e293b";
      ctx.fillText(fixture.category.toUpperCase(), centerTop.x, centerTop.y - 2);
      ctx.restore();
    });

    // Dimension indicators
    ctx.save();
    ctx.font = "600 11px 'Inter', sans-serif";
    ctx.fillStyle = "#64748b";
    const dimNorth = project(roomW / 2, -4, 0);
    ctx.fillText(`${(roomW / 12).toFixed(1)}′`, dimNorth.x, dimNorth.y);
    const dimWest = project(-4, roomL / 2, 0);
    ctx.fillText(`${(roomL / 12).toFixed(1)}′`, dimWest.x, dimWest.y);
    ctx.restore();
  }, [layout, yaw, pitch, zoom, selectedProductId]);

  return (
    <div className="canvas-3d-wrapper">
      {/* 3D Truth & Visualization Status Banner */}
      <div className="canvas-3d-banner">
        <div className="banner-truth-tag">
          <span className="badge-3d-status">VISUALIZATION AID</span>
          <span className="truth-text">
            3D perspective reflects computed 2D spatial coordinates. Spatial engineering intent is verified on the 2D plan.
          </span>
        </div>
        <div className="canvas-3d-controls-hint">
          <span>🖱 Drag to Orbit · Scroll to Zoom</span>
        </div>
      </div>

      {/* Interactive 3D Canvas */}
      <div className="canvas-3d-viewport">
        <canvas
          ref={canvasRef}
          className="canvas-3d-element"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          onClick={handleClick}
        />

        {/* Orbit Action Buttons */}
        <div className="canvas-3d-floating-toolbar">
          <button
            type="button"
            className="btn-orbit-tool"
            onClick={() => {
              setYaw(45);
              setPitch(35);
              setZoom(1.1);
            }}
            title="Reset to default architectural isometric angle"
          >
            ↺ Reset Angle
          </button>
          <button
            type="button"
            className="btn-orbit-tool"
            onClick={() => setZoom((z) => Math.min(2.0, z + 0.2))}
            title="Zoom In"
          >
            ＋
          </button>
          <button
            type="button"
            className="btn-orbit-tool"
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))}
            title="Zoom Out"
          >
            －
          </button>
        </div>
      </div>
    </div>
  );
};
