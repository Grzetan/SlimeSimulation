#version 430
in vec2 fragTexCoord;
out vec4 outColor;

uniform sampler2D inputTexture;

void main() {
    outColor = texture(inputTexture, fragTexCoord);
}