public class GenWhileNoUpdateFix011 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
            stock--;
        }
    }
}
