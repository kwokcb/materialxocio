
// lin_p3d65_scene to lin_rec709 function. Texture count: 0

vec4 mx_lin_p3d65_scene_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.2249401762805545, -0.042056954709687636, -0.019637554590334446, 0., -0.22494017628056287, 1.0420569547096903, -0.078636045550631917, 0., -0., 0., 1.0982736001409681, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
