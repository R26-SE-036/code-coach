public class GenMissingBreakBug033 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "expired";
            case 4:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int largest2(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }
}
