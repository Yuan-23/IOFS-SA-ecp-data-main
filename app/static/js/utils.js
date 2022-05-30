/**
 * This is the prototype of exist funcion
 * it is regeistered to the jQuery codetree.
 */
 (function($) {
    $.fn.exist = function(){
        if($(this).length>=1){
            return true;
        }
        return false;
    };
})(jQuery);