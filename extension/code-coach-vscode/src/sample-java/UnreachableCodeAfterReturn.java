public class UnreachableCodeAfterReturn {
    public static int doubleValue(int value) {
        return value * 2;
        // this line can never run
    }

    public static int tripleValue(int value) {
        return value * 3;
    }

    public static void main(String[] args) {
        int result = doubleValue(5);
        System.out.println(result);
        return;
        System.out.println("done");
    }
}
