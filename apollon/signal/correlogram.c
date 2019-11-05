#include "correlogram.h"

double
corrcoef (const double *data,
          const size_t  off_x,
          const size_t  off_y,
          const size_t  n)
{
    double  s_x     = 0.0;
    double  s_y     = 0.0;
    double  s_xy    = 0.0;
    double  s_sq_x  = 0.0;
    double  s_sq_y  = 0.0;
    double  cov     = 0.0;
    double  ms_x    = 0.0;
    double  ms_y    = 0.0;
    double  p_std   = 0.0;
    const size_t max_iter = off_x + n;

    for (size_t i = off_x, j = off_y; i < max_iter; i++, j++)
    {
        double  xi = data[i];
        double  yi = data[j];

        s_x     += xi;
        s_y     += yi;
        s_xy    += xi * yi;
        s_sq_x  += xi * xi;
        s_sq_y  += yi * yi;
    }

    cov     = s_xy - s_x * s_y / n;
    ms_x    = s_x * s_x / n;
    ms_y    = s_y * s_y / n;
    p_std   = sqrt (s_sq_x - ms_x) * sqrt (s_sq_y - ms_y);

    if (p_std == 0)
    {
        fprintf (stderr, "Zero division encoutered in corrcoef.");
        return -2;
    }

    return cov / p_std;
}


int
correlogram_delay (const double *sig,
                   const size_t *delays,
                   const size_t  wlen,
                   const size_t *dims,
                         double *cgram)
{

    for (size_t i = 0; i < dims[0]; i++)
    {
        for (size_t t = 0; t < dims[1]; t++)
        {
            double r = corrcoef (sig, t, t+delays[i], wlen);
            //printf ("(%zu, %zu) -> %zu\t", i, j, (j-1)*max_iter+i);
            if (r == -2)
            {
                fprintf (stderr, "corrcoef failed in correlogram.\n");
                return 0;
            }
            cgram[i*dims[1]+t] = r > 0.0F ? pow(r, 4) : 0.0F;
        }
        //printf ("\n");
    }
    return 1;
}

int
correlogram (const double *sig,
             const size_t  wlen,
             const size_t *dims,
                   double *cgram)
{

    for (size_t delay = 1; delay < dims[0]; delay++)
    {
        for (size_t off = 0; off < dims[1]; off++)
        {
            double r = corrcoef (sig, off, off+delay, wlen);
            //printf ("(%zu, %zu) -> %zu\t", i, j, (j-1)*max_iter+i);
            if (r == -2)
            {
                fprintf (stderr, "corrcoef failed in correlogram.\n");
                return 0;
            }
            cgram[(delay-1)*dims[1]+off] = r > 0.0F ? pow(r, 4) : 0.0F;
        }
    }
    return 1;
}