import { Composition } from "remotion";
import { Video } from "./Video";
import { TOTAL_FRAMES } from "./timing";

export const Root = () => {
  return (
    <Composition
      id="Video"
      component={Video}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
