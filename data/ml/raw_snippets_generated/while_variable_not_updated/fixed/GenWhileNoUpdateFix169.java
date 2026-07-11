public class GenWhileNoUpdateFix169 {
    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
            stock--;
        }
    }
}
