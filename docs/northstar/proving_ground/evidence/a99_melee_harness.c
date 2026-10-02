/* A99 round 2: sustained-melee harness. usage: a99_melee_harness MIL GAP STEPS [dump_file]
 * MIL = region-0 military (58.5 units per point, capped at OM_MAX_UNITS 10100).
 * GAP = clear gap between block edges after teleporting the player block next to the
 * enemy block; both sides get attack-move toward the other side's centroid.
 * GAP < 0 = idle opening (no staging, no commands). Per-step CLOCK_MONOTONIC around
 * om_tactical_step; stops after STEPS or when one side is dead. */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "ouroboros_sim.h"
#define OM_UT_WARDEN 3
#define OM_UT_BASTION 5
#ifdef PHASE /* scratch build whose unit.c has per-phase timers (not committed); see the report */
extern double om_ph[16],om_ph_dr_calls;
static const char*PN[9]={"refresh_pos","ai_tick","aura_regen","backswing","ability_adv","macro_tick","support","mission_tick","dmg_reduction(in ai)"};
#endif
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
static int cmp(const void*a,const void*b){double x=*(double*)a,y=*(double*)b;return x<y?-1:x>y;}
static double pct(double*s,int n,double p){int i=(int)(n*p);if(i>=n)i=n-1;return s[i];}
int main(int argc,char**argv){
  double mil=atof(argv[1]),gap=atof(argv[2]);int steps=atoi(argv[3]);
  om_world*W=om_world_new(80,121);
  uint32_t *pl,*en;int np=0,ne=0;
  const char*bare=getenv("BARE"); /* BARE=N: N units per side of a plain mix, no mission; WARD=percent wardens */
  if(bare){
    int per=atoi(bare),wp=getenv("WARD")?atoi(getenv("WARD")):0,cols=(int)ceil(sqrt(per*2.0));
    pl=malloc(per*4);en=malloc(per*4);np=per;ne=per;
    static const int mix[4]={0,2,1,4};
    for(int side=0;side<2;side++)for(int i=0;i<per;i++){
      int ty=(i%100<wp)?3:mix[i%4];double x=(i%cols)*18.0+(side?cols*18.0+gap:0),y=(i/cols)*18.0;
      uint32_t u=om_unit_spawn(W,ty,side+1,x,y,0);(side?en:pl)[i]=u;}
    printf("bare per_side=%d ward_pct=%d\n",per,wp);
    om_command_attack_move(W,pl,np,cols*18.0*2+gap,0);om_command_attack_move(W,en,ne,0,0);
    goto run;
  }
  for(int i=0;i<8;i++) om_world_set_feature(W,(om_feature)i,1);
  om_world_generate(W);om_events_load_launch(W);om_mission_load_launch_library(W);om_campaign_start(W,1);
  for(int i=0;i<10;i++)om_world_step(W);
  for(uint32_t r=0;r<om_region_count(W);r++)om_mission_refresh_context(W,(int32_t)r);
  om_region_set(W,0,om_region_tier(W,0),mil,om_region_field(W,0,OM_F_ECONOMY),om_region_field(W,0,OM_F_TENSION),om_region_field(W,0,OM_F_POPULATION),0,0,om_region_owner(W,0));
  om_mission_setup(W,0,1,0);om_mission_begin(W);
  uint32_t n=om_unit_count(W),pf=om_player_faction(W);
  pl=malloc(n*4);en=malloc(n*4);
  double pcx=0,pcy=0,ecx=0,ecy=0;
  for(uint32_t u=1;u<=n;u++){ if(!om_unit_alive(W,u))continue; double x,y;om_unit_get_pos(W,u,&x,&y);
    if(om_unit_get_faction(W,u)==pf){pl[np++]=u;pcx+=x;pcy+=y;}else{en[ne++]=u;ecx+=x;ecy+=y;}}
  pcx/=np;pcy/=np;ecx/=ne;ecy/=ne;
  int nw=0,nb=0;for(int i=0;i<np;i++){int t=om_unit_get_unit_type(W,pl[i]);nw+=t==OM_UT_WARDEN;nb+=t==OM_UT_BASTION;}
  int enw=0,enb=0;for(int i=0;i<ne;i++){int t=om_unit_get_unit_type(W,en[i]);enw+=t==OM_UT_WARDEN;enb+=t==OM_UT_BASTION;}
  printf("mil=%.1f player=%d enemy=%d wardens p/e=%d/%d bastions p/e=%d/%d\n",mil,np,ne,nw,enw,nb,enb);
  if(gap>=0){
    double d=hypot(pcx-ecx,pcy-ecy),ux=(pcx-ecx)/d,uy=(pcy-ecy)/d,rp=0,re=0;
    for(int i=0;i<np;i++){double x,y;om_unit_get_pos(W,pl[i],&x,&y);double r=hypot(x-pcx,y-pcy);if(r>rp)rp=r;}
    for(int i=0;i<ne;i++){double x,y;om_unit_get_pos(W,en[i],&x,&y);double r=hypot(x-ecx,y-ecy);if(r>re)re=r;}
    double dist=gap+rp+re,tx=ecx+ux*dist,ty=ecy+uy*dist;
    for(int i=0;i<np;i++){double x,y;om_unit_get_pos(W,pl[i],&x,&y);om_unit_set_pos(W,pl[i],x+tx-pcx,y+ty-pcy);}
    om_command_attack_move(W,pl,np,ecx,ecy);
    om_command_attack_move(W,en,ne,tx,ty);
  }
  run:;
#ifdef PHASE
  double*ph=calloc((size_t)steps*9,sizeof(double)),*drc=calloc(steps,sizeof(double));
#endif
  double*t=malloc(steps*sizeof(double));FILE*df=argc>4?fopen(argv[4],"w"):NULL;int done=0;uint64_t ck=1469598103934665603ull;
  for(int s=0;s<steps;s++){
#ifdef PHASE
    double before[9],cb=om_ph_dr_calls;for(int k=0;k<9;k++)before[k]=om_ph[k];
#endif
    double a=now();om_tactical_step(W);t[s]=now()-a;done=s+1;
    if(getenv("CK")){ /* FNV-1a over every unit's alive/pos/hp bits plus the world checksum, chained over steps */
      for(uint32_t u=1;u<=om_unit_count(W);u++){double x=0,y=0,h=om_unit_get_hp(W,u);om_unit_get_pos(W,u,&x,&y);
        uint64_t b[4]={om_unit_alive(W,u),*(uint64_t*)&x,*(uint64_t*)&y,*(uint64_t*)&h};
        for(int k=0;k<4;k++)for(int j=0;j<8;j++){ck^=(b[k]>>(8*j))&255;ck*=1099511628211ull;}}
      ck^=om_world_checksum(W);ck*=1099511628211ull;}
#ifdef PHASE
    for(int k=0;k<9;k++)ph[(size_t)s*9+k]=om_ph[k]-before[k];drc[s]=om_ph_dr_calls-cb;
#endif
    int ap=0,ae=0;
    if(s%25==0||s==steps-1){for(int i=0;i<np;i++)ap+=om_unit_alive(W,pl[i]);for(int i=0;i<ne;i++)ae+=om_unit_alive(W,en[i]);
      if(df)fprintf(df,"%d %.3f %d %d\n",s,t[s],ap,ae);
      if(s%100==0)printf("step %d: ms=%.2f alive p=%d e=%d period=%u\n",s,t[s],ap,ae,om_tactical_tick_period(W));
      if(gap>=0&&(ap==0||ae==0)){break;}}
    else if(df)fprintf(df,"%d %.3f\n",s,t[s]);
  }
  double*sd=malloc(done*sizeof(double));for(int i=0;i<done;i++)sd[i]=t[i];qsort(sd,done,sizeof(double),cmp);
  double sum=0;for(int i=0;i<done;i++)sum+=t[i];
  int ap=0,ae=0;for(int i=0;i<np;i++)ap+=om_unit_alive(W,pl[i]);for(int i=0;i<ne;i++)ae+=om_unit_alive(W,en[i]);
  printf("RESULT steps=%d alive_end p=%d e=%d median=%.2f p95=%.2f p99=%.2f max=%.2f mean=%.2f total_s=%.1f\n",done,ap,ae,pct(sd,done,.5),pct(sd,done,.95),pct(sd,done,.99),sd[done-1],sum/done,sum/1000);
#ifdef PHASE
  {int worst=0;for(int i=0;i<done;i++)if(t[i]>t[worst])worst=i;
   printf("PHASE ms: phase | total | share_of_total | median_step | worst_step(#%d)\n",worst);
   for(int k=0;k<9;k++){double tot=0,*c=malloc(done*sizeof(double));for(int i=0;i<done;i++){c[i]=ph[(size_t)i*9+k];tot+=c[i];}
     qsort(c,done,sizeof(double),cmp);printf("PHASE %-20s %10.1f %5.1f%% %8.3f %8.3f\n",PN[k],tot,100*tot/sum,c[done/2],ph[(size_t)worst*9+k]);}
   printf("PHASE damage_reduction calls=%.0f total, %.0f in worst step\n",om_ph_dr_calls,drc[worst]);}
#endif
  if(getenv("CK"))printf("CHAIN %llu\n",(unsigned long long)ck);
  return 0;}
