<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"
  xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <NamedLayer>
    <Name>earnings</Name>
    <UserStyle>
      <Title>earnings</Title>
      <FeatureTypeStyle>
       <Rule>
         <Name>1</Name>
         <Title>less than £462</Title>
         <ogc:Filter>
           <ogc:PropertyIsLessThan>
             <ogc:PropertyName>median</ogc:PropertyName>
             <ogc:Literal>462</ogc:Literal>
           </ogc:PropertyIsLessThan>
         </ogc:Filter>
         <PolygonSymbolizer>
           <Fill>
             <CssParameter name="fill">#f2f0f7</CssParameter>
             <CssParameter name="fill-opacity">1</CssParameter>
           </Fill>
         </PolygonSymbolizer>
       </Rule>
       <Rule>
         <Name>2</Name>
         <Title>from £462 to £490</Title>
         <ogc:Filter>
           <ogc:And>
             <ogc:PropertyIsGreaterThanOrEqualTo>
               <ogc:PropertyName>median</ogc:PropertyName>
               <ogc:Literal>462</ogc:Literal>
             </ogc:PropertyIsGreaterThanOrEqualTo>
             <ogc:PropertyIsLessThan>
               <ogc:PropertyName>median</ogc:PropertyName>
               <ogc:Literal>490</ogc:Literal>
             </ogc:PropertyIsLessThan>
           </ogc:And>
         </ogc:Filter>
         <PolygonSymbolizer>
           <Fill>
             <CssParameter name="fill">#cbc9e2</CssParameter>
             <CssParameter name="fill-opacity">1</CssParameter>
           </Fill>
         </PolygonSymbolizer>
       </Rule>
       <Rule>
         <Name>3</Name>
         <Title>from £490 to £538</Title>
         <ogc:Filter>
           <ogc:And>
             <ogc:PropertyIsGreaterThanOrEqualTo>
               <ogc:PropertyName>median</ogc:PropertyName>
               <ogc:Literal>490</ogc:Literal>
             </ogc:PropertyIsGreaterThanOrEqualTo>
             <ogc:PropertyIsLessThan>
               <ogc:PropertyName>median</ogc:PropertyName>
               <ogc:Literal>538</ogc:Literal>
             </ogc:PropertyIsLessThan>
           </ogc:And>
         </ogc:Filter>
         <PolygonSymbolizer>
           <Fill>
             <CssParameter name="fill">#9e9ac8</CssParameter>
             <CssParameter name="fill-opacity">1</CssParameter>
           </Fill>
         </PolygonSymbolizer>
       </Rule>
       <Rule>
         <Name>4</Name>
         <Title>over £538</Title>
         <ogc:Filter>
           <ogc:PropertyIsGreaterThan>
             <ogc:PropertyName>median</ogc:PropertyName>
             <ogc:Literal>538</ogc:Literal>
           </ogc:PropertyIsGreaterThan>
         </ogc:Filter>
         <PolygonSymbolizer>
           <Fill>
             <CssParameter name="fill">#6a51a3</CssParameter>
             <CssParameter name="fill-opacity">1</CssParameter>
           </Fill>
         </PolygonSymbolizer>
       </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
