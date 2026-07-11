public class GenCleanGeneric032 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
