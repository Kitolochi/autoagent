# After Effects ExtendScript Gotchas

Silent failures and workarounds for the CEP bridge + ExtendScript pipeline.

## Text Layers

- `new TextDocument()` is unusable. Create layer first, then modify:
  ```js
  var layer = comp.layers.addText("Hello");
  var doc = layer.sourceText.value;
  doc.fontSize = 36;
  doc.fillColor = [1, 1, 1];
  doc.font = "Arial-BoldMT";
  layer.sourceText.setValue(doc);
  ```

## Effects

- **Drop Shadow color**: property name is `"Shadow Color"`, NOT `"Color"`
- **No duplicate effects**: adding same effect twice throws "Object is invalid". Precomp the layer instead
- **ADBE Glow fails on text layers**: use Drop Shadow with Distance=0 as substitute
- **ADBE Stroke**: traces entire layer boundary, not mask shapes. Use shape layer strokes
- **Opacity ranges vary by effect**:
  - Stroke Opacity: 0-1
  - Drop Shadow Opacity: 0-255
  - Noise Amount: 0-100
- **Transform Effect**: display names fail. Use matchNames: `ADBE Geometry2-0003` (Scale Height), `ADBE Geometry2-0004` (Scale Width)
- **ADBE Grid**: rectangular cells only. Build custom grids with shape layers

## Masks

- Use direct properties, not `.property()` strings:
  ```js
  mask.maskMode = MaskMode.SUBTRACT;
  mask.maskFeather.setValue([300, 300]);
  mask.property("ADBE Mask Shape").setValue(shapePath);
  ```
- **Bezier ellipse**: 4-point approximation, kappa = 0.5522847498
- **Rounded rect mask**: 12-point vertex array, tangent offsets = radius * 0.55

## Layers & Rendering

- **Solid layers bleed through blur**: even 200px Gaussian Blur shows rectangular edges. Use shape layer ellipses
- **Layer move API**: check layer is not already at target position before `moveAfter()`/`moveBefore()`
- **3D material options darken content**: "Accepts Lights" darkens. Use ADD-blend overlay for ambient light
- **Individual 3D layers misalign under rotation**: each rotates around own anchor. Precomp first, then 3D

## Expression Patterns

Key reusable expressions for the build pipeline:

- **Universal Fade**: `linear()`/`ease()` with multiplication for composable in/hold/out
- **Pulse/Breathe**: sine wave. Freq guide: 0.01=glacial(~10s), 0.05=calm(~2s), 0.12=heartbeat(~0.9s)
- **Card Entrance**: 22-frame ease-in, position offset 500px to 0px
- **Animated Dash**: `timeToFrames(time) * -2.5` for stroke flow
- **Typing Animation**: map time to character count, 15-frame cursor blink cycle
- **Looping Scale (Ring Pulse)**: 180-frame cycles with staggered offset per instance
- **Wrapping Position**: modulo-based reset for particle recycling
- **Wiggle**: `wiggle(60, 10)` for randomized subtle motion
- **TypeScript escaping**: newlines as `\\n`, use `.join('\\n')`, template literals for variable embedding

## Bridge Architecture & Timing

The CEP panel polls every 250ms for `.jsx` commands written by Node.js to a temp directory. Results come back as `.json`. The `send()` function wraps code with error handling, polls with 45s timeout.

**Critical sleep intervals between `send()` calls:**

| Operation | Required Delay |
|---|---|
| Normal step | 200ms |
| After comp creation | 300ms |
| After heavy shape ops (96+ groups) | 1000ms |

- **Critical vs non-critical**: critical operations abort on failure (exit process). Non-critical return error objects
- **Helper functions auto-injected**: tick conversion for time props, comp/folder lookup with defensive error handling for bad project items
- **Verification**: use `saveFrameToPng()` frame export as primary check during automated builds. Visual verification catches issues that code-level checks miss
- **Heavy shape warning**: creating 96+ shape groups in a single `send()` can freeze AE temporarily. Break into batches with 1000ms breathing room
