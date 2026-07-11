public class GenCleanGeneric009 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
