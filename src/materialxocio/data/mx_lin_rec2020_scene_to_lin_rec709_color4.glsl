
// lin_rec2020_scene to lin_rec709 function. Texture count: 0

vec4 mx_lin_rec2020_scene_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.6604910021084354, -0.12455047452159097, -0.018150763354905279, 0., -0.58764113878854762, 1.1328998971259598, -0.10057889800800768, 0., -0.072849863319883981, -0.0083494226043701082, 1.118729661362905, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
