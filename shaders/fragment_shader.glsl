#version 430
in vec2 fragTexCoord;
out vec4 outColor;

layout (r8, binding = 1) uniform image2D backgroundTexture;

uniform sampler2D inputTexture;

void main() {
    ivec2 texSize = imageSize(backgroundTexture);
    ivec2 pixelCoord = ivec2(fragTexCoord * texSize);
    pixelCoord = clamp(pixelCoord, ivec2(0), texSize - 1);
    vec4 texelValue = imageLoad(backgroundTexture, pixelCoord);

    if(abs(texelValue.r - 0.87058823529) < 0.00001){
        vec4 color = texture(inputTexture, fragTexCoord);
        outColor = vec4(1.0 - color.r, 1.0 - color.g, 1.0 - color.b, 1.0);
    } else {
        vec4 calculatedColor;
        if(texelValue.r > 0.4){
            calculatedColor = vec4(0.0, 0.0, 0.0, 1.0);
        } else {
            calculatedColor = vec4(texelValue.r, texelValue.r, texelValue.r, 1.0);
        }
        outColor = vec4(calculatedColor.rgb * step(calculatedColor.rgb, vec3(0.5)), 1.0);
    }
}