import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { addItem } from '../actions/action-cart';

class ItemList extends Component {
  addCart = (obj) => {
    console.log(obj);
    this.props.addItem(obj);
  }
  render() {
    return (
      <div className="table-responsive">
        <table className="table table-xs table-hover">
            <thead>
                <tr className="bg-primary">
                    <th>Add</th>
                    <th>Product</th>
                    <th>SKU</th>
                    <th>Quantity</th>
                    <th>Selling Price</th>
                </tr>
            </thead>
            <tbody>
            {this.props.items.results.map(obj => {
              return (
                <tr key={obj.id}>
                    <td onClick={() => { this.addCart(obj); } }>
                      <span className="cursor-pointer btn btn-primary btn-sm">
                        <i className="icon-cart-add"></i>
                      </span>
                    </td>
                    <td>{obj.productName}</td>
                    <td>{obj.sku}</td>
                    <td>{obj.quantity}</td>
                    <td>{obj.price}</td>
                </tr>
              );
            })
            }
            {this.props.items.length === 0 &&
            <tr>
                <td colSpan='3' className="text-center">
                    <h4>No data Found</h4>
                </td>
            </tr>
            }
            </tbody>
        </table>
      </div>
    );
  }
}

ItemList.propTypes = {
  items: PropTypes.array.isRequired,
  addItem: PropTypes.func
};
function mapStateToProps(state) {
  return {
    items: state.items
  };
}

function matchDispatchToProps(dispatch) {
  return bindActionCreators({
    addItem
  }, dispatch);
}
export default connect(mapStateToProps, matchDispatchToProps)(ItemList);
