public class GenMissingBreakBug075 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "archived";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
