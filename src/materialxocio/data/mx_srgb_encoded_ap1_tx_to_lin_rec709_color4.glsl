
// srgb_encoded_ap1_tx to lin_rec709 function. Texture count: 0

vec4 mx_srgb_encoded_ap1_tx_to_lin_rec709_color4(vec4 inPixel)
{
  vec4 outColor = inPixel;
  
  // Add Gamma 'monCurveFwd' processing
  
  {
    vec4 breakPnt = vec4(0.0392857157, 0.0392857157, 0.0392857157, 1.);
    vec4 slope = vec4(0.077380158, 0.077380158, 0.077380158, 1.);
    vec4 scale = vec4(0.947867274, 0.947867274, 0.947867274, 0.999998987);
    vec4 offset = vec4(0.0521326996, 0.0521326996, 0.0521326996, 9.99998974e-07);
    vec4 gamma = vec4(2.4000001, 2.4000001, 2.4000001, 1.00000095);
    vec4 isAboveBreak = vec4(greaterThan( outColor, breakPnt));
    vec4 linSeg = outColor * slope;
    vec4 powSeg = pow( max( vec4(0., 0., 0., 0.), scale * outColor + offset), gamma);
    vec4 res = isAboveBreak * powSeg + ( vec4(1., 1., 1., 1.) - isAboveBreak ) * linSeg;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }
  
  // Add Matrix processing
  
  {
    vec4 res = vec4(outColor.rgb.r, outColor.rgb.g, outColor.rgb.b, outColor.a);
    vec4 tmp = res;
    res = mat4(1.7050509926579756, -0.13025641750704287, -0.02400335680461799, 0., -0.62179212065700873, 1.1408047365754079, -0.12896897606497126, 0., -0.083258872000981698, -0.010548319068357195, 1.152972332869586, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
