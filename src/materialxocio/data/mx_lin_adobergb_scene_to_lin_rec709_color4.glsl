
// lin_adobergb_scene to lin_rec709 function. Texture count: 0

vec4 mx_lin_adobergb_scene_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
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
