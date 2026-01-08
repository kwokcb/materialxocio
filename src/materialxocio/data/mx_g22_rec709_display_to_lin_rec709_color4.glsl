
// g22_rec709_display to lin_rec709 function. Texture count: 0

vec4 mx_g22_rec709_display_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Gamma 'basicMirrorFwd' processing
  
  {
    vec4 gamma = vec4(2.2000000000000002, 2.2000000000000002, 2.2000000000000002, 1.);
    vec4 signcol = sign(outColor);;
    vec4 res = signcol * pow( abs( outColor ), gamma );
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
