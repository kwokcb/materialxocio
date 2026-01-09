
// g22_adobergb_scene to lin_rec709 function. Texture count: 0

vec4 mx_g22_adobergb_scene_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Gamma 'basicPassThruFwd' processing
  
  {
    vec4 gamma = vec4(2.19921875, 2.19921875, 2.19921875, 1.);
    vec4 breakPnt = vec4(0., 0., 0., 0.);
    vec4 isAboveBreak = vec4(greaterThan( outColor, breakPnt));
    vec4 powSeg = pow(max( vec4(0., 0., 0., 0.), outColor ), gamma);
    vec4 res = isAboveBreak * powSeg + ( vec4(1., 1., 1., 1.) - isAboveBreak ) * outColor;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.3983557439607741, -0., -0., 0., -0.39835574396077833, 1., -0.042928989294473863, 0., -0., -0., 1.0429289892944664, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
