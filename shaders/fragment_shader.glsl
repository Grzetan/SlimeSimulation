#version 430
in vec2 fragTexCoord;
out vec4 outColor;

uniform sampler2D inputTexture;

void main() {
    vec4 color = texture(inputTexture, fragTexCoord);
    if(color == vec4(1.0)){
        outColor = color; // can change to other color to visualize agents
    } else {
        outColor = color;
    }
}