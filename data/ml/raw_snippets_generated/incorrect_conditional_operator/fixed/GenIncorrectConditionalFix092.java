public class GenIncorrectConditionalFix092 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static void announce(int budget) {
        if (budget == 5) {
            System.out.println("hit the target");
        }
    }
}
