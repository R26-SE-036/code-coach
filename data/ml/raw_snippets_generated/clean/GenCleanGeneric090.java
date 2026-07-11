public class GenCleanGeneric090 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int sum2(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }
}
