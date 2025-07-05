import { register } from "../app";
import { CognitoIdentityProviderClient, SignUpCommand } from "@aws-sdk/client-cognito-identity-provider";

jest.mock("@aws-sdk/client-cognito-identity-provider", () => {
    const mClient = { send: jest.fn() };
    return {
        CognitoIdentityProviderClient: jest.fn(() => mClient),
        SignUpCommand: jest.fn((args) => args)
    };
});

describe("register()", () => {
    beforeEach(() => jest.clearAllMocks());

    test("400 si faltan datos", async () => {
        const res = await register({ body: JSON.stringify({ email: "a@b.c" }) });
        expect(res.statusCode).toBe(400);
    });

    test("201 y llamada a Cognito cuando datos correctos", async () => {
        const res = await register({ body: JSON.stringify({ email: "a@b.c", password: "Passw0rd!" }) });
        expect(res.statusCode).toBe(201);
        const client = CognitoIdentityProviderClient.mock.results[0].value;
        expect(client.send).toHaveBeenCalledWith(expect.any(SignUpCommand));
    });

    test("500 en error de Cognito", async () => {
        const client = CognitoIdentityProviderClient.mock.results[0].value;
        client.send.mockRejectedValueOnce(new Error("fail"));
        const res = await register({ body: JSON.stringify({ email: "x@y.z", password: "P@sswd123" }) });
        expect(res.statusCode).toBe(500);
        expect(JSON.parse(res.body)).toHaveProperty("error");
    });
});
