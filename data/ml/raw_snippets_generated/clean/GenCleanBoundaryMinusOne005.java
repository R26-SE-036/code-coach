public class GenCleanBoundaryMinusOne005 {
    static int tally(int[] values) {
        int total = 0;
        for (int i = 0; i <= values.length - 1; i++) {
            total += values[i];
        }
        return total;
    }

    static void printAll1(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
