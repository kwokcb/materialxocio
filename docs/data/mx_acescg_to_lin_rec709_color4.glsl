
// Declaration of the OCIO shader function

vec4 mx_acescg_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.7050509926579815, -0.1302564175070435, -0.024003356804618046, 0., -0.62179212065700573, 1.140804736575405, -0.12896897606497093, 0., -0.083258872000979672, -0.010548319068357662, 1.1529723328695858, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
