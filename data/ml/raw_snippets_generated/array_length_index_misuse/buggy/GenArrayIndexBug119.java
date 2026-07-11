public class GenArrayIndexBug119 {
    static String describe1(int limit) {
        if (limit < 100) {
            return "low";
        } else if (limit > 500) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }
}
