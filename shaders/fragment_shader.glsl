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
    if(texelValue.r == 0.87058823529){
        vec4 color = texture(inputTexture, fragTexCoord);
        if(color == vec4(1.0)){
            outColor = color; // can change to other color to visualize agents
        } else {
            outColor = color;
        }
    }else{
        outColor = vec4(texelValue.r, texelValue.r, texelValue.r, 1.0);
    }
}