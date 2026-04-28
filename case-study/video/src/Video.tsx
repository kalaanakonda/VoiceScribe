import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { COLORS } from "./tokens";
import { SCENES } from "./timing";
import { DotGrid } from "./components/DotGrid";

import { Title } from "./scenes/Title";
import { Colors } from "./scenes/Colors";
import { Type } from "./scenes/Type";
import { Icon } from "./scenes/Icon";
import { PillScene } from "./scenes/PillScene";
import { States } from "./scenes/States";
import { Buttons } from "./scenes/Buttons";
import { Toggle } from "./scenes/Toggle";
import { Cards } from "./scenes/Cards";
import { Outro } from "./scenes/Outro";

export const Video: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: COLORS.bg }}>
      {/* Persistent dotted-grid backdrop, present for the whole video. */}
      <DotGrid />

      {/* Scene content sits above the backdrop. */}
      <AbsoluteFill style={{ zIndex: 1 }}>
      <Sequence from={SCENES.title.from} durationInFrames={SCENES.title.duration}>
        <Title />
      </Sequence>
      <Sequence from={SCENES.colors.from} durationInFrames={SCENES.colors.duration}>
        <Colors />
      </Sequence>
      <Sequence from={SCENES.type.from} durationInFrames={SCENES.type.duration}>
        <Type />
      </Sequence>
      <Sequence from={SCENES.icon.from} durationInFrames={SCENES.icon.duration}>
        <Icon />
      </Sequence>
      <Sequence from={SCENES.pill.from} durationInFrames={SCENES.pill.duration}>
        <PillScene />
      </Sequence>
      <Sequence from={SCENES.states.from} durationInFrames={SCENES.states.duration}>
        <States />
      </Sequence>
      <Sequence from={SCENES.buttons.from} durationInFrames={SCENES.buttons.duration}>
        <Buttons />
      </Sequence>
      <Sequence from={SCENES.toggle.from} durationInFrames={SCENES.toggle.duration}>
        <Toggle />
      </Sequence>
      <Sequence from={SCENES.cards.from} durationInFrames={SCENES.cards.duration}>
        <Cards />
      </Sequence>
      <Sequence from={SCENES.outro.from} durationInFrames={SCENES.outro.duration}>
        <Outro />
      </Sequence>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
