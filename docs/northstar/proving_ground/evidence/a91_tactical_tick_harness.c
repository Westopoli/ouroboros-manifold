#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "ouroboros_sim.h"
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
static int cmp(const void*a,const void*b){double x=*(double*)a,y=*(double*)b;return x<y?-1:x>y;}
static om_world *build(double mil, int *live, int *nplayer){
  om_world *W=om_world_new(80,121);
  for(int i=0;i<8;i++) om_world_set_feature(W,(om_feature)i,1);
  om_world_generate(W); om_events_load_launch(W); om_mission_load_launch_library(W);
  om_campaign_start(W,1);
  for(int i=0;i<10;i++) om_world_step(W);
  for(uint32_t r=0;r<om_region_count(W);r++) om_mission_refresh_context(W,(int32_t)r);
  if(mil>0){ uint32_t r=0;
    om_region_set(W,r,om_region_tier(W,r),mil,om_region_field(W,r,OM_F_ECONOMY),om_region_field(W,r,OM_F_TENSION),om_region_field(W,r,OM_F_POPULATION),0,0,om_region_owner(W,r)); }
  om_mission_setup(W,0,1,0);
  om_mission_begin(W);
  *live=0;*nplayer=0;
  for(uint32_t u=1;u<=om_unit_count(W);u++) if(om_unit_alive(W,u)){(*live)++; if(om_unit_get_faction(W,u)==om_player_faction(W))(*nplayer)++;}
  return W;
}
int main(int argc,char**argv){
  double mil=atof(argv[1]); int nt=argc>2?atoi(argv[2]):30; int warm=argc>3?atoi(argv[3]):5;
  int live,np; om_world*W=build(mil,&live,&np);
  printf("mil=%.2f spawned_live=%d player=%d enemy=%d enemy_power=%.0f\n",mil,live,np,live-np,om_mission_get_enemy_power(W));
  if(argc>4){ /* count only */ return 0;}
  for(int i=0;i<warm;i++) om_tactical_step(W);
  double *t=malloc(nt*sizeof(double));
  for(int i=0;i<nt;i++){double a=now();om_tactical_step(W);t[i]=now()-a;}
  int live2=0; for(uint32_t u=1;u<=om_unit_count(W);u++) if(om_unit_alive(W,u)) live2++;
  if(getenv("DUMP")){for(int i=0;i<nt;i++)fprintf(stderr,"%d %.2f\n",i,t[i]);} double mean=0;for(int i=0;i<nt;i++)mean+=t[i];mean/=nt;printf("mean=%.3f ",mean); double s[1000]; for(int i=0;i<nt;i++) s[i]=t[i]; qsort(s,nt,sizeof(double),cmp);
  printf("steps=%d live_after=%d period=%u median_ms=%.3f p95_ms=%.3f min=%.3f max=%.3f\n",nt,live2,om_tactical_tick_period(W),s[nt/2],s[(int)(nt*0.95)>=nt?nt-1:(int)(nt*0.95)],s[0],s[nt-1]);
  return 0;}
