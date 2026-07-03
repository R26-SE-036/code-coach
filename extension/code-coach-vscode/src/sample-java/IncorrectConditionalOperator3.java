public class IncorrectConditionalOperator3 {
    static boolean checkConnection(int statusCode) {
        boolean connected = false;
        if (connected = statusCode == 200) {
            System.out.println("Connected successfully");
        } else {
            System.out.println("Connection failed");
        }
        return connected;
    }

    public static void main(String[] args) {
        checkConnection(200);
        checkConnection(404);
    }
}
