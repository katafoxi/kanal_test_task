import React from 'react';
import Card from 'react-bootstrap/Card'
import { MDBTypography } from 'mdb-react-ui-kit';

const CardTotal = (props) => {
    return (<>
    <Card className="align-items-center">
        <Card className="mt-5 " border="dark" style={{ width: '70%' , align:'center'}}>
            <Card.Header  className="fs-1 text-center " style={{background: 'black', color:'white'}} >Total, USD</Card.Header>
            <Card.Body>
                <MDBTypography tag='div' className='text-center  display-1 pb-3 mb-3 border-bottom'>
                    {props.total}
                </MDBTypography>
            </Card.Body>
        </Card>
        <br />
        </Card>
    </>
    );
};

export default CardTotal;