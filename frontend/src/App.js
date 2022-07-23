import React, { useEffect, useState } from 'react'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import TTable from "./components/Table";
import Graphic from "./components/Graphic";
import CardTotal from "./components/CardTotal";

const baseURL = 'http://localhost:8000'

const App = () => {
    const [contracts, setContracts] = useState([])

    const Total = contracts.reduce((contractsTotal, contracts) => contractsTotal + contracts.price_usd, 0);

    const getAllContracts = async () => {
        const response = await fetch(`${baseURL}/contracts/`);
        const data = await response.json()

        if (response.ok) {
            console.log(data)
            setContracts(data)
        } else {
            console.log("Failed Network Request")
        }
    }

    useEffect(
        () => {
            getAllContracts()
        }, []
    )

    return (
        <Container fluid>
            <Row className="justify-content-md-center mt-5">
                <Col>
                    <Graphic contracts={contracts} />
                </Col>
                <Col >
                    <CardTotal total={Total} />
                    <TTable contracts={contracts} />
                </Col>
            </Row>
        </Container>
    )
}

export default App;