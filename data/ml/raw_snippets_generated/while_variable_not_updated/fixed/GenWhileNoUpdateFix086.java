public class GenWhileNoUpdateFix086 {
    static void pump(boolean loaded, int stock) {
        while (!loaded) {
            System.out.println(stock);
            stock++;
            loaded = stock > 10;
        }
    }
}
