public class GenMissingBreakBug144 {
    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
            case 2:
                label = "archived";
                break;
            case 3:
                label = "paid";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
