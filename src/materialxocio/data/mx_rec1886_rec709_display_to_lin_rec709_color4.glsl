
// rec1886_rec709_display to lin_rec709 function. Texture count: 0

vec4 mx_rec1886_rec709_display_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Gamma 'basicFwd' processing
  
  {
    vec4 gamma = vec4(2.3999999999999999, 2.3999999999999999, 2.3999999999999999, 1.);
    vec4 res = pow( max( vec4(0., 0., 0., 0.), outColor ), gamma );
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
