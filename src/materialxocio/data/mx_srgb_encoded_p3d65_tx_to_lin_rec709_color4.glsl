
// srgb_encoded_p3d65_tx to lin_rec709 function. Texture count: 0

vec4 mx_srgb_encoded_p3d65_tx_to_lin_rec709_color4(vec4 inPixel)
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
    res = mat4(1.2249401762805545, -0.042056954709687636, -0.019637554590334446, 0., -0.22494017628056287, 1.0420569547096903, -0.078636045550631917, 0., -0., 0., 1.0982736001409681, 0., 0., 0., 0., 1.) * tmp;
    outColor.rgb = vec3(res.x, res.y, res.z);
    outColor.a = res.w;
  }

  return outColor;
}
