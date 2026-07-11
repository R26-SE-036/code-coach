public class GenCleanTailIndex025 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static int tail(int[] values) {
        return values[values.length - 1];
    }
}
