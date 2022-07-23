import React from 'react';
import Table from 'react-bootstrap/Table'
import { MDBTable, MDBTableHead, MDBTableBody } from 'mdb-react-ui-kit';

const TTable = (props) => {
    return (
        <MDBTable small table position-relative variant="primary" className="mt-5">
            <MDBTableHead dark>
                <tr>
                    <th>№</th>
                    <th>Заказ №</th>
                    <th>Стоимость,$</th>
                    <th>Срок поставки</th>
                </tr>
            </MDBTableHead>
            <MDBTableBody>
                {props.contracts.map(contracts => (
                    <tr key={contracts.id} className='table-info'>
                        <td>{contracts.id}</td>
                        <td>{contracts.contract}</td>
                        <td>{contracts.price_usd}</td>
                        <td>{contracts.date}</td>
                    </tr>
                ))}
            </MDBTableBody>
        </MDBTable>
    );
};

export default TTable;