
// p3d65_display to lin_rec709 function. Texture count: 0

vec4 mx_p3d65_display_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Gamma 'basicFwd' processing
  
  {
    vec4 gamma = vec4(2.6000000000000001, 2.6000000000000001, 2.6000000000000001, 1.);
    vec4 res = pow( max( vec4(0., 0., 0., 0.), outColor ), gamma );
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.2249401762805601, -0.042056954709688135, -0.019637554590334505, 0., -0.22494017628055812, 1.0420569547096905, -0.07863604555063225, 0., -0., 0., 1.0982736001409614, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
