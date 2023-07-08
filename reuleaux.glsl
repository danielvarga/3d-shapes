// https://www.shadertoy.com/view/DdXfDM

// Daniel Varga plugging his manifold into raymarching example by Inigo Quilez. Thanks Inigo!

// The MIT License
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

// https://iquilezles.org/articles/distfunctions

#define PI                          3.1415926535897932

precision highp float;


float dot2(in vec3 v ) { return dot(v,v); }

float dot2(in vec2 v ) { return dot(v,v); }


vec2 complexMul(vec2 z1, vec2 z2) {
    return vec2(z1.x * z2.x - z1.y * z2.y, z1.x * z2.y + z1.y * z2.x);
}


vec2 cartesianToPolar(vec2 cartesian) {
    float radius = length(cartesian);
    float angle = atan(cartesian.y, cartesian.x);
    return vec2(radius, angle);
}

vec2 polarToCartesian(vec2 polar) {
    float x = polar.x * cos(polar.y);
    float y = polar.x * sin(polar.y);
    return vec2(x, y);
}


// exact, meaning it can be pumped up correctly.
float sdEquilateralTriangle( in vec2 p, in float r )
{
    const float k = sqrt(3.0);
    p.x = abs(p.x) - r;
    p.y = p.y + r/k;
    if( p.x+k*p.y>0.0 ) p = vec2(p.x-k*p.y,-k*p.x-p.y)/2.0;
    p.x -= clamp( p.x, -2.0*r, 0.0 );
    return -length(p)*sign(p.y);
}


// nonexact, meaning pumping it up is not faithful.
// R is roundness parameter.
// R>>1 is flat, R=1 is Reuleaux, 0.5<R<1 is rounder.
float sdReuleauxTriangle(vec2 p, float R) 
{
    // unit triangle with center in the origin.
    vec2 C0 = vec2(0.5773502692, 0.0),
         C1 = vec2(-0.2886751346, 0.5),
         C2 = vec2(-0.2886751346, -0.5);

    float x = sqrt(R*R - 0.25) + C1.x;

    // dual triangle.
    // when drawing radius R circles from Ds, they intersect in the Cs.
    vec2 D0 = x * vec2(-0.5, 0.8660254038),
         D1 = x * vec2(1.0, 0.0),
         D2 = x * vec2(-0.5, -0.8660254038);

    // the distance to the farthest D, minus R.
    return max(max(length(p - D0), length(p - D1)), length(p - D2)) - R;
}


// from https://www.shadertoy.com/view/tlXGW4
// not currently used
float regular( int n, float a )
{
    float ang = PI/float(n);

    return cos(ang)/cos(a - ang * (2.0 * floor(0.5 * a/ang) + 1.0));
}


// twist_ratio 1/3 means turn the cross-section
// 1/3 while turning the plane once.
float manifold(vec3 p,
        float outer_radius, float inner_radius,
        float twist_ratio,
        float twist_offset)
{
    vec2 rot = normalize(p.xy);
    float plane_angle = atan(rot.y, rot.x);
    float twist_angle = plane_angle * twist_ratio;

    twist_angle += twist_offset;

    vec2 twist = polarToCartesian(vec2(1.0, twist_angle));

    vec2 pp = vec2(sqrt(dot2(p.xy)) - outer_radius, p.z) / inner_radius;
    vec2 rotpp = complexMul(pp, twist);

    return sdReuleauxTriangle(rotpp, 1.0);
    float roundedness = 0.05;
    return sdEquilateralTriangle(rotpp, 0.5) - roundedness;
}


float map( in vec3 pos )
{
    float mul = 10.0;
    float inner_radius = 1.5;
    float outer_radius = sin(iTime / 2.0) + 4.0;
    float twist_ratio = 1.0 / 3.0;
    float twist_offset = 1.0 * iTime;
    return manifold(mul * pos,
        outer_radius, inner_radius,
        twist_ratio, twist_offset) * 0.01;
}


// https://iquilezles.org/articles/normalsSDF
vec3 calcNormal( in vec3 pos )
{
    vec2 e = vec2(1.0,-1.0)*0.5773;
    const float eps = 0.0005;
    return normalize( e.xyy*map( pos + e.xyy*eps ) + 
                      e.yyx*map( pos + e.yyx*eps ) + 
                      e.yxy*map( pos + e.yxy*eps ) + 
                      e.xxx*map( pos + e.xxx*eps ) );
}

// Daniel: let's rather just hardwire no AA.
#define AA 0


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // camera movement  
    float an = 1.0 * iTime;
    // float an = 0.0;
    vec3 ro = vec3( 1.0*cos(an), 0.4, 1.0*sin(an) );
    vec3 ta = vec3( 0.0, 0.0, 0.0 );
    // camera matrix
    vec3 ww = normalize( ta - ro );
    vec3 uu = normalize( cross(ww,vec3(0.0,1.0,0.0) ) );
    vec3 vv = normalize( cross(uu,ww));

    vec3 tot = vec3(0.0);

    #if AA>1
    for( int m=0; m<AA; m++ )
    for( int n=0; n<AA; n++ )
    {
        // pixel coordinates
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        vec2 p = (-iResolution.xy + 2.0*(fragCoord+o))/iResolution.y;
        #else
        vec2 p = (-iResolution.xy + 2.0*fragCoord.xy)/iResolution.y;
        #endif

        // create view ray
        vec3 rd = normalize( p.x*uu + p.y*vv + 1.5*ww );

        // raymarch
        const float tmax = 10.0;
        float t = 0.0;
        for( int i=0; i<1000; i++ )
        {
            vec3 pos = ro + t*rd;
            float h = map(pos);
            if( h<0.001 || t>tmax ) break;
            t += h;
        }

        // shading/lighting
        vec3 col = vec3(0.0);
        if( t<tmax )
        {
            vec3 pos = ro + t*rd;
            vec3 nor = calcNormal(pos);
            float dif = clamp( dot(nor,vec3(0.57703)), 0.0, 1.0 );
            float amb = 0.5 + 0.5*dot(nor,vec3(0.0,1.0,0.0));
            col = vec3(0.2,0.3,0.4)*amb + vec3(0.8,0.7,0.5)*dif;
            col *= 2.0*exp2(-t / 1.5);
        }

        // gamma        
        col = sqrt( col );
        tot += col;
    #if AA>1
    }
    tot /= float(AA*AA);
    #endif

    fragColor = vec4( tot, 1.0 );
}
