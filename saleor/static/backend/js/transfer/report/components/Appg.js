import React from 'react';
import { Query } from 'react-apollo';
import gql from 'graphql-tag';

/**
 * COMPONENTS
 */
import Loader from './Loader';

const ExchangeRates = () => (
  <Query
    query={gql`
      {
        allCounterTransfer(page:1) {
          page
          pages
          total
          hasNext
          hasPrev
            objects {
              id, date, counterTransferItems {
                id, sku, counter {
                  id, name
                }
              }
            }
        }
      }
    `}
  >
    {({ loading, error, data }) => {
      if (loading) return <Loader />;
      if (error) return <Loader />;
      console.log(data.allCounterTransfer.objects);
      return <Loader />;
    }}
  </Query>
);

export default ExchangeRates;
