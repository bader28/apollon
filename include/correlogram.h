#ifndef CORRELOGRAM_H
#define CORRELOGRAM_H

#include <math.h>
#include <stdio.h>


double
corrcoef (const double *data,
          const size_t  off_x,
          const size_t  off_y,
          const size_t  n);

int
correlogram_delay (const double *sig,
                   const size_t *delays,
                   const size_t  wlen,
                   const size_t *dims,
                         double *cgram);

int
correlogram (const double *sig,
             const size_t  wlen,
             const size_t *dims,
                   double *cgram);

#endif  /* CORRELOGRAM_H */
